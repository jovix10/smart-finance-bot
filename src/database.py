import sqlite3
import pandas as pd
import hashlib

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def configurar_banco():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    # Tabela de transações com coluna de dono (usuario_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT,
            Data TEXT,
            Descricao TEXT,
            Valor REAL,
            Categoria TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (username)
        )
    ''')
    conn.commit()
    conn.close()

def salvar_no_banco(df, username):
    conn = sqlite3.connect('finance.db')
    # Adiciona a coluna do dono antes de salvar
    df['usuario_id'] = username
    # Salva no banco (append)
    df.to_sql('transacoes', conn, if_exists='append', index=False)
    
    # Limpeza de duplicatas apenas para este usuário específico
    query = f"DELETE FROM transacoes WHERE rowid NOT IN (SELECT min(rowid) FROM transacoes GROUP BY usuario_id, Data, Descricao, Valor)"
    conn.execute(query)
    conn.commit()
    conn.close()

def carregar_do_banco(username):
    conn = sqlite3.connect('finance.db')
    try:
        # O PULO DO GATO: Filtramos os dados pelo usuário logado
        query = "SELECT Data, Descricao, Valor, Categoria FROM transacoes WHERE usuario_id = ?"
        df = pd.read_sql(query, conn, params=(username,))
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()

# Funções de Auth
def cadastrar_usuario(usuario, senha):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', 
                       (usuario, hash_senha(senha)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_usuario(usuario, senha):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?', 
                   (usuario, hash_senha(senha)))
    res = cursor.fetchone()
    conn.close()
    return res