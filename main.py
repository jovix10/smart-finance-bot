import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys
import sqlite3
import requests

# Garantir acesso aos módulos locais
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from processor import processar_dados, processar_dados_manual, gerar_pdf, obter_icone
from database import *

# Configuração da página
st.set_page_config(page_title="Financially Pro", layout="wide", page_icon="📈")
configurar_banco()

# CSS Moderno (Ajustado para a Logo e Validações)
st.markdown("""
    <style>
    /* Estilização das Métricas (Cards) */
    [data-testid="stMetric"] {
        background-color: rgba(151, 166, 195, 0.08);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(151, 166, 195, 0.15);
    }
    
    /* Botões Modernos */
    .stButton>button { 
        border-radius: 8px; 
        font-weight: bold; 
        transition: all 0.2s;
    }
    
    /* Inputs Arredondados */
    .stTextInput>div>div>input { border-radius: 8px; }
    
    /* Centralizar a logo na tela de login */
    .logo-container {
        text-align: center;
        margin-bottom: 30px;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para renderizar a Logo em CSS (Moderna e Adaptativa)
def renderizar_logo():
    st.markdown("""
        <div class="logo-container">
            <div style="
                display: inline-block;
                padding: 15px 25px;
                border-radius: 15px;
                background: linear-gradient(135deg, #0052cc 0%, #002e73 100%);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <span style="
                    font-family: 'Trebuchet MS', sans-serif;
                    font-size: 32px;
                    font-weight: bold;
                    color: white;
                    letter-spacing: -1px;
                ">
                    Financially<span style="color: #66b3ff;">Pro</span>
                </span>
            </div>
            <p style="margin-top: 10px; color: gray; font-size: 14px;">Seu controle financeiro profissional</p>
        </div>
        """, unsafe_allow_html=True)

if 'logado' not in st.session_state: st.session_state['logado'] = False

# --- TELA DE ACESSO (LOGIN/CADASTRO) ---
if not st.session_state['logado']:
    
    # Renderiza a Logo no topo
    renderizar_logo()
    
    t1, t2 = st.tabs(["Acessar Conta", "Criar Nova Conta"])
    
    with t1:
        st.subheader("Login")
        u = st.text_input("Nome de Usuário (Username)", key="login_user")
        p = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar", key="btn_login"):
            if login_usuario(u, p):
                st.session_state['logado'] = True
                st.session_state['username'] = u
                st.rerun()
            else: st.error("Nome de usuário ou senha incorretos.")

    with t2:
        st.subheader("Cadastro")
        st.info("💡 Importante: Escolha um Nome de Usuário único. Não pedimos e-mail.")
        nu = st.text_input("Defina seu Nome de Usuário", key="reg_user")
        np = st.text_input("Defina sua Senha", type="password", key="reg_pass")
        
        # O processor.py obter_icone foi mantido para compatibilidade, 
        # mas emojis foram removidos da lógica de cadastro aqui.
        if st.button("Finalizar Cadastro", key="btn_reg"):
            if not nu or not np:
                st.warning("Preecha o usuário e a senha.")
            elif len(np) < 4:
                st.warning("A senha deve ter pelo menos 4 caracteres.")
            else:
                # database.cadastrar_usuario já faz a checagem de duplicidade
                if cadastrar_usuario(nu, np):
                    st.success("Conta criada com sucesso! Agora vá para a aba 'Acessar Conta'.")
                else:
                    # Esta é a acusação de que o usuário já existe
                    st.error("⚠️ Este Nome de Usuário já está em uso. Por favor, escolha outro.")

else:
    # --- INTERFACE PRINCIPAL (LOGADO) ---
    with st.sidebar:
        # Mini logo no sidebar
        st.markdown("<h2 style='text-align: center; color: #0052cc;'>F-Pro</h2>", unsafe_allow_html=True)
        st.write(f"Usuário: **{st.session_state['username']}**")
        st.divider()
        
        # Navegação com ícones de sistema (Material Icons)
        menu = st.radio("Navegar", ["Dashboard", "Lançamentos", "Histórico", "Ajustes"])
        
        st.divider()
        st.subheader("Câmbio do Dia")
        try:
            # Usando a versão robusta da requisição com User-Agent e Timeout
            res = requests.get(
                "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL", 
                timeout=5,
                headers={'User-Agent': 'FinanciallyPro/2.0'}
            )
            if res.status_code == 200:
                data = res.json()
                st.metric("Dólar (USD)", f"R$ {float(data['USDBRL']['bid']):.2f}")
                st.metric("Euro (EUR)", f"R$ {float(data['EURBRL']['bid']):.2f}")
            else:
                st.caption("Serviço de câmbio indisponível.")
        except Exception:
            st.caption("Erro ao conectar com serviço de câmbio.")
        
        st.divider()
        if st.button("Sair da Conta"):
            st.session_state['logado'] = False
            st.rerun()

    # Carregar dados do usuário
    df_user = carregar_do_banco(st.session_state['username'])
    conn = sqlite3.connect('finance.db')
    user_row = conn.execute("SELECT salario FROM usuarios WHERE username=?", (st.session_state['username'],)).fetchone()
    salario = user_row[0] if user_row else 0.0
    conn.close()

    # --- ABA: DASHBOARD ---
    if menu == "Dashboard":
        st.title("Painel Geral")
        c1, c2, c3 = st.columns(3)
        total = df_user['Valor'].sum() if not df_user.empty else 0
        
        c1.metric("Receita Atual", f"R$ {salario:,.2f}")
        c2.metric("Total Despesas", f"R$ {total:,.2f}", delta=f"{(total/salario*100 if salario>0 else 0):.1f}% da receita", delta_color="inverse")
        c3.metric("Balanço Livre", f"R$ {salario - total:,.2f}")

        st.divider()
        col_a, col_b = st.columns([6, 4])
        
        with col_a:
            st.subheader("Distribuição de Gastos")
            if not df_user.empty:
                # Usando o esquema de cores padrão do tema para modernidade
                fig = px.pie(df_user, values='Valor', names='Categoria', hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
                fig.update_layout(showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("Adicione lançamentos para visualizar os gráficos.")

        with col_b:
            st.subheader("Acompanhamento de Metas")
            df_metas = carregar_metas(st.session_state['username'])
            if not df_metas.empty:
                for _, m in df_metas.iterrows():
                    gasto_cat = df_user[df_user['Categoria'] == m['categoria']]['Valor'].sum() if not df_user.empty else 0
                    prog = min(gasto_cat / m['valor_limite'], 1.0)
                    
                    st.write(f"**{m['categoria']}** (R$ {gasto_cat:,.2f} de R$ {m['valor_limite']:,.2f})")
                    if prog >= 1.0:
                        st.progress(prog)
                        st.error("Limite excedido!")
                    elif prog >= 0.8:
                        st.progress(prog)
                        st.warning("Próximo ao limite.")
                    else:
                        st.progress(prog)
            else: st.caption("Vá em Ajustes para definir suas metas mensais.")

    # --- ABA: LANÇAMENTOS ---
    elif menu == "Lançamentos":
        st.title("Adicionar Transação")
        st.markdown("Use o formulário abaixo para lançar despesas manualmente.")
        
        with st.form("add_gasto", clear_on_submit=True):
            col1, col2 = st.columns(2)
            d = col1.date_input("Data da Transação")
            v = col2.number_input("Valor (R$)", min_value=0.01, step=0.50)
            desc = st.text_input("Descrição (Ex: Assinatura Netflix, Almoço)")
            
            if st.form_submit_button("Registrar Gasto"):
                if not desc:
                    st.error("A descrição é obrigatória.")
                else:
                    df_new = pd.DataFrame({"Data":[d], "Descricao":[desc], "Valor":[v]})
                    # processor.definir_categoria já cuida de categorizar sem emojis
                    df_final = processar_dados_manual(df_new)
                    salvar_no_banco(df_final, st.session_state['username'])
                    st.success(f"Gasto de R$ {v:.2f} registrado em {df_final['Categoria'][0]}!")
                    # Pequeno delay para o usuário ver a mensagem antes de limpar
                    import time
                    time.sleep(1)
                    st.rerun()

    # --- ABA: HISTÓRICO ---
    elif menu == "Histórico":
        st.title("Histórico de Transações")
        if not df_user.empty:
            # Mostra a tabela limpa, ordenada pela data mais recente
            st.dataframe(
                df_user.sort_values('Data', ascending=False), 
                use_container_width=True,
                hide_index=True
            )
            
            st.divider()
            # Botão de exportação
            pdf_bytes = gerar_pdf(df_user, st.session_state['username'])
            st.download_button(
                label="Baixar Relatório Completo (PDF)", 
                data=pdf_bytes, 
                file_name=f"extrato_{st.session_state['username']}.pdf", 
                mime="application/pdf",
                key="btn_pdf"
            )
        else: st.warning("Nenhuma transação encontrada para este usuário.")

    # --- ABA: AJUSTES ---
    elif menu == "Ajustes":
        st.title("Configurações da Conta")
        
        # Seção de Salário
        st.subheader("Receita Base")
        col_s1, col_s2 = st.columns([4, 2])
        with col_s1:
            n_sal = st.number_input("Definir Salário Mensal Padrão (R$)", value=salario, min_value=0.0)
        with col_s2:
            st.write("#") # Espaçador
            if st.button("Salvar Salário"):
                atualizar_salario(st.session_state['username'], n_sal)
                st.success("Salário atualizado com sucesso!")
                st.rerun()
        
        st.divider()
        
        # Seção de Metas
        st.subheader("Orçamento por Categoria (Metas)")
        st.markdown("Defina quanto você pretende gastar no máximo em cada categoria por mês.")
        
        col_m1, col_m2, col_m3 = st.columns([4, 4, 2])
        with col_m1:
            cat = st.selectbox("Selecione a Categoria", ["ALIMENTACAO", "TRANSPORTE", "LAZER", "SAUDE", "FIXO", "SUPERMERCADO", "ASSINATURAS"])
        with col_m2:
            lim = st.number_input("Definir Limite (R$)", min_value=10.0, step=10.0)
        with col_m3:
            st.write("#") # Espaçador
            if st.button("Definir Meta"):
                definir_meta(st.session_state['username'], cat, lim)
                st.success(f"Meta para {cat} definida!")
                st.rerun()