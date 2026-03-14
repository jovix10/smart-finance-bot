import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

# Ajuste de Path para Linux/Pop!_OS
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from processor import processar_dados, processar_dados_manual
from database import configurar_banco, salvar_no_banco, carregar_do_banco, cadastrar_usuario, login_usuario

st.set_page_config(page_title="FinançApp Pro", layout="wide")
configurar_banco()

# Estado da Sessão
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# --- TELA DE ACESSO ---
if not st.session_state['logado']:
    st.title("🔐 Bem-vindo ao FinançApp")
    t1, t2 = st.tabs(["Login", "Criar Conta"])
    with t1:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if login_usuario(u, p):
                st.session_state['logado'] = True
                st.session_state['username'] = u
                st.rerun()
            else: st.error("Erro de login.")
    with t2:
        nu = st.text_input("Novo Usuário")
        np = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            if cadastrar_usuario(nu, np): st.success("Sucesso! Faça login.")
            else: st.error("Usuário já existe.")

# --- APP PRINCIPAL ---
else:
    with st.sidebar:
        st.title(f"Olá, {st.session_state['username']}")
        menu = st.radio("Menu", ["📊 Dashboard", "📥 Adicionar Gastos"])
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.rerun()

    if menu == "📊 Dashboard":
        df = carregar_do_banco(st.session_state['username'])
        if not df.empty:
            st.metric("Total", f"R$ {df['Valor'].sum():,.2f}")
            st.plotly_chart(px.pie(df, values='Valor', names='Categoria', hole=0.4))
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum dado cadastrado.")

    elif menu == "📥 Adicionar Gastos":
        modo = st.selectbox("Método", ["Manual", "Planilha (CSV)"])
        if modo == "Manual":
            with st.form("manual"):
                d = st.date_input("Data")
                desc = st.text_input("Descrição")
                v = st.number_input("Valor", min_value=0.0)
                if st.form_submit_button("Salvar"):
                    df_m = pd.DataFrame({"Data":[d], "Descricao":[desc], "Valor":[v]})
                    df_final = processar_dados_manual(df_m)
                    salvar_no_banco(df_final, st.session_state['username'])
                    st.success("Gasto salvo!")
                    st.rerun()
        else:
            f = st.file_uploader("Suba seu CSV")
            if f:
                df_f = processar_dados(f)
                if st.button("Salvar Tudo"):
                    salvar_no_banco(df_f, st.session_state['username'])
                    st.success("Planilha importada!")
                    st.rerun()