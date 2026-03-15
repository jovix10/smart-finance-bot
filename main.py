import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
import sqlite3
import requests

# Garantir acesso aos módulos locais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from processor import processar_dados, processar_dados_manual, gerar_pdf
from database import *

# Configuração da página e inicialização
st.set_page_config(page_title="Financially Pro", layout="wide", page_icon="🏦")
configurar_banco()

# CSS Adaptativo para Light/Dark Mode
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(151, 166, 195, 0.1);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(151, 166, 195, 0.2);
    }
    .stButton>button { border-radius: 8px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# Lógica de Sessão
if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    st.title("🔐 Bem-vindo ao Financially")
    t1, t2 = st.tabs(["Entrar", "Cadastrar"])
    with t1:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Acessar Conta"):
            if login_usuario(u, p):
                st.session_state['logado'] = True
                st.session_state['username'] = u
                st.rerun()
            else: st.error("Usuário ou senha incorretos")
    with t2:
        nu = st.text_input("Novo Usuário")
        np = st.text_input("Nova Senha", type="password")
        if st.button("Criar Conta"):
            if cadastrar_usuario(nu, np): st.success("Conta criada com sucesso!")
            else: st.error("Este usuário já existe")

else:
    # --- APP LOGADO ---
    with st.sidebar:
        st.title(f"👋 Olá, {st.session_state['username']}")
        menu = st.radio("Navegar", ["🏦 Home", "📤 Adicionar", "📅 Histórico", "⚙️ Ajustes"])
        
        st.divider()
        st.subheader("💱 Câmbio Real-time")
        try:
            req = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL").json()
            st.write(f"💵 Dólar: **R$ {float(req['USDBRL']['bid']):.2f}**")
            st.write(f"💶 Euro: **R$ {float(req['EURBRL']['bid']):.2f}**")
        except: st.write("Câmbio indisponível")
        
        if st.button("🚪 Sair"):
            st.session_state['logado'] = False
            st.rerun()

    # Carregar dados
    df_user = carregar_do_banco(st.session_state['username'])
    conn = sqlite3.connect('finance.db')
    user_row = conn.execute("SELECT salario FROM usuarios WHERE username=?", (st.session_state['username'],)).fetchone()
    salario = user_row[0] if user_row else 0.0
    conn.close()

    if menu == "🏦 Home":
        st.title("Painel Financeiro")
        c1, c2, c3 = st.columns(3)
        total_gasto = df_user['Valor'].sum() if not df_user.empty else 0
        
        c1.metric("Minha Receita", f"R$ {salario:,.2f}")
        c2.metric("Total Gasto", f"R$ {total_gasto:,.2f}", delta=f"{(total_gasto/salario*100 if salario>0 else 0):.1f}%")
        c3.metric("Saldo Livre", f"R$ {salario - total_gasto:,.2f}")

        st.divider()
        st.subheader("🎯 Acompanhamento de Metas")
        df_metas = carregar_metas(st.session_state['username'])
        if not df_metas.empty:
            for _, m in df_metas.iterrows():
                gasto_cat = df_user[df_user['Categoria'] == m['categoria']]['Valor'].sum() if not df_user.empty else 0
                prog = min(gasto_cat / m['valor_limite'], 1.0)
                st.write(f"**{m['categoria']}** (Limite: R$ {m['valor_limite']})")
                st.progress(prog)
        else: st.info("Defina metas na aba Ajustes.")

    elif menu == "📤 Adicionar":
        st.title("Alimentar Sistema")
        modo = st.selectbox("Forma de entrada", ["Manual", "Planilha (CSV)"])
        if modo == "Manual":
            with st.form("manual"):
                d = st.date_input("Data")
                desc = st.text_input("Descrição do Gasto")
                v = st.number_input("Valor (R$)", min_value=0.0)
                if st.form_submit_button("Lançar"):
                    df_manual = pd.DataFrame({"Data":[d], "Descricao":[desc], "Valor":[v]})
                    df_final = processar_dados_manual(df_manual)
                    salvar_no_banco(df_final, st.session_state['username'])
                    st.success("Salvo com sucesso!")
                    st.rerun()
        else:
            f = st.file_uploader("Suba seu CSV")
            if f:
                df_f = processar_dados(f)
                st.dataframe(df_f.head())
                if st.button("Confirmar Importação"):
                    salvar_no_banco(df_f, st.session_state['username'])
                    st.success("Importado!")
                    st.rerun()

    elif menu == "📅 Histórico":
        st.title("Histórico de Transações")
        if not df_user.empty:
            st.dataframe(df_user.sort_values('Data', ascending=False), use_container_width=True)
            pdf_bytes = gerar_pdf(df_user, st.session_state['username'])
            st.download_button("📥 Baixar PDF", pdf_bytes, "relatorio.pdf", "application/pdf")
        else: st.warning("Sem dados.")

    elif menu == "⚙️ Ajustes":
        st.title("Configurações")
        n_sal = st.number_input("Atualizar Salário", value=salario)
        if st.button("Salvar Salário"):
            atualizar_salario(st.session_state['username'], n_sal)
            st.success("Atualizado!")
        
        st.divider()
        st.subheader("Definir Metas")
        cat = st.selectbox("Categoria", ["ALIMENTACAO", "TRANSPORTE", "LAZER", "SAUDE", "FIXO"])
        lim = st.number_input("Limite (R$)", min_value=0.0)
        if st.button("Salvar Meta"):
            definir_meta(st.session_state['username'], cat, lim)
            st.success("Meta Salva!")