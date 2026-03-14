import pandas as pd

# Esta é a nossa "IA" de categorização. Ela fica fora das funções para ser reutilizada.
def definir_categoria(descricao):
    desc = str(descricao).upper()
    regras = {
        'ALIMENTACAO': ['IFOOD', 'RESTAURANTE', 'LANCHONETE', 'BURGER', 'PIZZA', 'CAFE', 'ALMOCO', 'PADARIA'],
        'SUPERMERCADO': ['MERCADO', 'EXTRA', 'CARREFOUR', 'BH', 'CONFIANCA', 'ATACADAO'],
        'TRANSPORTE': ['UBER', '99APP', 'POSTO', 'GASOLINA', 'SHELL', 'IPIRANGA', 'AUTO'],
        'ASSINATURAS': ['NETFLIX', 'SPOTIFY', 'AMAZON', 'DISNEY', 'HBO', 'CANVA'],
        'SAUDE': ['FARMACIA', 'DROGASIL', 'UNIMED', 'HOSPITAL', 'MEDICO'],
        'LAZER': ['CINEMA', 'SHOPPING', 'VIAGEM', 'HOTEL', 'BAR']
    }
    for categoria, palavras in regras.items():
        if any(palavra in desc for palavra in palavras):
            return categoria
    return 'OUTROS'

def processar_dados(file):
    try:
        df = pd.read_csv(file, skipinitialspace=True)
        if df.empty: return pd.DataFrame()
        
        # Padroniza nomes de colunas
        df.columns = [col.strip().capitalize() for col in df.columns]
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        
        # Aplica a categorização
        df['Categoria'] = df['Descricao'].apply(definir_categoria)
        return df
    except Exception as e:
        print(f"Erro no processamento: {e}")
        return pd.DataFrame()

def processar_dados_manual(df):
    # Processa a entrada única do formulário
    df['Categoria'] = df['Descricao'].apply(definir_categoria)
    df['Data'] = pd.to_datetime(df['Data'])
    return df