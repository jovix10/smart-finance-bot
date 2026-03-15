import pandas as pd
from fpdf import FPDF
import unicodedata

def normalizar_texto(texto):
    # Remove acentos e deixa em maiúsculo para a "IA" não errar
    return "".join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn').upper().strip()

def definir_categoria(descricao):
    desc = normalizar_texto(descricao)
    
    # "Cérebro" do sistema: Regras de associação inteligente
    regras = {
        'ALIMENTACAO': ['IFOOD', 'RESTAURANTE', 'PADARIA', 'LANCHONETE', 'BURGER', 'PIZZA', 'CAFE', 'ALMOCO', 'JANTA', 'DOCE', 'SORVETE'],
        'SUPERMERCADO': ['MERCADO', 'EXTRA', 'CARREFOUR', 'BH', 'ATACADAO', 'COMPRAS', 'FEIRA', 'DESPENSA'],
        'TRANSPORTE': ['UBER', '99APP', 'POSTO', 'GASOLINA', 'SHELL', 'IPIRANGA', 'ONIBUS', 'PEDAGIO', 'ESTACIONAMENTO'],
        'ASSINATURAS': ['NETFLIX', 'SPOTIFY', 'AMAZON', 'DISNEY', 'CANVA', 'YOUTUBE', 'CLOUD', 'GAME'],
        'SAUDE': ['FARMACIA', 'DROGASIL', 'HOSPITAL', 'UNIMED', 'DENTISTA', 'MEDICO', 'EXAME'],
        'LAZER': ['CINEMA', 'SHOPPING', 'BAR', 'SHOW', 'HOTEL', 'VIAGEM', 'FESTA', 'CERVEJA', 'PUB'],
        'FIXO': ['ALUGUEL', 'LUZ', 'INTERNET', 'CONDOMINIO', 'AGUA', 'MATRICULA', 'CURSO', 'FACULDADE']
    }
    
    for categoria, palavras in regras.items():
        if any(palavra in desc for palavra in palavras):
            return categoria
    return 'OUTROS'

def processar_dados_manual(df):
    df['Categoria'] = df['Descricao'].apply(definir_categoria)
    df['Data'] = pd.to_datetime(df['Data'])
    return df

def processar_dados(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip().capitalize() for col in df.columns]
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        df['Categoria'] = df['Descricao'].apply(definir_categoria)
        return df
    except Exception:
        return pd.DataFrame()

def gerar_pdf(df, usuario):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"Relatorio Financeiro - {usuario}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Gasto Total: R$ {df['Valor'].sum():,.2f}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, "Data", 1)
    pdf.cell(80, 10, "Descricao", 1)
    pdf.cell(45, 10, "Categoria", 1)
    pdf.cell(35, 10, "Valor", 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(30, 10, str(row['Data'].date()), 1)
        pdf.cell(80, 10, str(row['Descricao'])[:30], 1)
        pdf.cell(45, 10, str(row['Categoria']), 1)
        pdf.cell(35, 10, f"R$ {row['Valor']:.2f}", 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')