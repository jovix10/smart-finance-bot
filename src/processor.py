import pandas as pd
from fpdf import FPDF

def definir_categoria(descricao):
    desc = str(descricao).upper()
    regras = {
        'ALIMENTACAO': ['IFOOD', 'RESTAURANTE', 'PADARIA', 'LANCHONETE', 'BURGER', 'PIZZA', 'CAFE'],
        'SUPERMERCADO': ['MERCADO', 'EXTRA', 'CARREFOUR', 'BH', 'ATACADAO'],
        'TRANSPORTE': ['UBER', '99APP', 'POSTO', 'GASOLINA', 'SHELL'],
        'ASSINATURAS': ['NETFLIX', 'SPOTIFY', 'AMAZON', 'DISNEY', 'CANVA'],
        'SAUDE': ['FARMACIA', 'DROGASIL', 'HOSPITAL', 'UNIMED'],
        'LAZER': ['CINEMA', 'SHOPPING', 'BAR', 'SHOW', 'HOTEL'],
        'FIXO': ['ALUGUEL', 'LUZ', 'INTERNET', 'CONDOMINIO']
    }
    for categoria, palavras in regras.items():
        if any(palavra in desc for keyword in palavras if (palavra := keyword) in desc):
            return categoria
    return 'OUTROS'

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

def processar_dados_manual(df):
    df['Categoria'] = df['Descricao'].apply(definir_categoria)
    df['Data'] = pd.to_datetime(df['Data'])
    return df

def gerar_pdf(df, usuario):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"Relatorio Financeiro - {usuario}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Gasto Total: R$ {df['Valor'].sum():,.2f}", ln=True)
    pdf.ln(5)
    
    # Cabeçalho da Tabela
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