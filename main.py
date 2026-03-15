import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
import sqlite3
import requests
import time

# Garantir acesso aos módulos locais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from processor import processar_dados, processar_dados_manual, gerar_pdf, obter_icone
from database import *

# Configuração da página
st.set_page_config(page_title="Financially Pro", layout="wide", page_icon="📈")
configurar_banco()

# CSS Moderno
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(151, 166, 195, 0.08);
        padding: 20px; border-radius: 12px; border: 1px solid rgba(151, 166, 195, 0.15);
    }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .logo-container { text-align: center; margin-bottom: 30px; padding: 20px; }
    </style>
    """, unsafe_allow_html=True)

def renderizar_logo():
    st.markdown("""
        <div class="logo-container">
            <div style="display: inline-block; padding: 15px 25px; border-radius: 15px; background: linear-gradient(135deg, #0052cc 0%, #002e73 100%);">
                <span style="font-family: sans-serif; font-size: 32px; font-weight: bold; color: white;">
                    Financially<span style="color: #66b3ff;">Pro</span>
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

if 'logado' not in st.session_state: st.session_state['logado'] = False

if not st.session_state['logado']:
    renderizar_logo()
    t1, t2 = st.tabs(["Login", "Criar Nova Conta"])
    with t1:
        u = st.text_input("Usuário", key="login_user")
        p = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar"):
            if login_usuario(u, p):
                st.session_state['logado'] = True
                st.session_state['username'] = u
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")
    with t2:
        st.info("💡 Nome de Usuário único (não é necessário e-mail).")
        nu = st.text_input("Novo Usuário", key="reg_user")
        np = st.text_input("Nova Senha", type="password", key="reg_pass")
        if st.button("Cadastrar"):
            if cadastrar_usuario(nu, np): st.success("Sucesso! Vá para Login.")
            else: st.error("⚠️ Este nome de usuário já está em uso.")

else:
    # --- INTERFACE PRINCIPAL ---
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #0052cc;'>F-Pro</h2>", unsafe_allow_html=True)
        st.write(f"Usuário: **{st.session_state['username']}**")
        st.divider()
        menu = st.radio("Menu", ["Dashboard", "Lançamentos", "Histórico", "Ajustes"])
        
        st.divider()
        st.subheader("Câmbio do Dia")
        
        # Lógica de Câmbio com Plano A e B
        if 'cotacoes' not in st.session_state:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                # Plano A: AwesomeAPI
                res = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL", headers=headers, timeout=5)
                if res.status_code == 200:
                    st.session_state['cotacoes'] = res.json()
                else:
                    # Plano B: Segunda tentativa ou API alternativa
                    time.sleep(1)
                    res = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL", headers=headers, timeout=5)
                    st.session_state['cotacoes'] = res.json() if res.status_code == 200 else None
            except:
                st.session_state['cotacoes'] = None

        if st.session_state['cotacoes']:
            c = st.session_state['cotacoes']
            st.metric("Dólar", f"R$ {float(c['USDBRL']['bid']):.2f}")
            st.metric("Euro", f"R$ {float(c['EURBRL']['bid']):.2f}")
        else:
            st.caption("⚠️ Erro ao carregar câmbio.")
        
        if st.button("Encerrar Sessão"):
            st.session_state['logado'] = False
            st.rerun()

    df_user = carregar_do_banco(st.session_state['username'])
    conn = sqlite3.connect('finance.db')
    user_row = conn.execute("SELECT salario FROM usuarios WHERE username=?", (st.session_state['username'],)).fetchone()
    salario = user_row[0] if user_row else 0.0
    conn.close()

    if menu == "Dashboard":
        st.title("Painel de Controle")
        c1, c2, c3 = st.columns(3)
        total = df_user['Valor'].sum() if not df_user.empty else 0
        c1.metric("Receita", f"R$ {salario:,.2f}")
        c2.metric("Despesas", f"R$ {total:,.2f}", delta=f"{(total/salario*100 if salario>0 else 0):.1f}%", delta_color="inverse")
        c3.metric("Saldo", f"R$ {salario - total:,.2f}")
        
        if not df_user.empty:
            fig = px.pie(df_user, values='Valor', names='Categoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    elif menu == "Lançamentos":
        st.title("Adicionar Gasto")
        with st.form("add_gasto"):
            d = st.date_input("Data")
            v = st.number_input("Valor (R$)", min_value=0.0)
            desc = st.text_input("Descrição")
            if st.form_submit_button("Lançar"):
                df_new = pd.DataFrame({"Data":[d], "Descricao":[desc], "Valor":[v]})
                df_final = processar_dados_manual(df_new)
                salvar_no_banco(df_final, st.session_state['username'])
                st.success("Registrado!")
                st.rerun()

    elif menu == "Histórico":
        st.title("Histórico")
        if not df_user.empty:
            st.dataframe(df_user.drop(columns=['id']).sort_values('Data', ascending=False), use_container_width=True)
            
            with st.expander("🗑️ Deletar uma transação"):
                df_user['label_delete'] = df_user['Data'].dt.strftime('%d/%m') + " - " + df_user['Descricao'] + " (R$ " + df_user['Valor'].astype(str) + ")"
                opcao_del = st.selectbox("Escolha o item:", df_user['label_delete'])
                id_para_deletar = df_user[df_user['label_delete'] == opcao_del]['id'].values[0]
                if st.button("Excluir Agora", type="primary"):
                    deletar_transacao(id_para_deletar)
                    st.rerun()
            
            pdf_bytes = gerar_pdf(df_user.drop(columns=['label_delete', 'id']), st.session_state['username'])
            st.download_button("Baixar PDF", pdf_bytes, "relatorio.pdf", "application/pdf")
        else: st.info("Sem dados.")

    elif menu == "Ajustes":
        st.title("Ajustes")
        n_sal = st.number_input("Salário Mensal", value=salario)
        if st.button("Salvar Salário"):
            atualizar_salario(st.session_state['username'], n_sal)
            st.rerun()
        
        st.divider()
        cat = st.selectbox("Categoria da Meta", ["ALIMENTACAO", "TRANSPORTE", "LAZER", "SAUDE", "FIXO", "SUPERMERCADO", "ASSINATURAS"])
        lim = st.number_input("Limite Máximo", min_value=0.0)
        if st.button("Definir Meta"):
            definir_meta(st.session_state['username'], cat, lim)
            st.success("Meta Ativa!")