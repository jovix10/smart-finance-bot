import sqlite3
import pandas as pd
import hashlib

def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def configurar_banco():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT,
            salario REAL DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metas (
            usuario_id TEXT,
            categoria TEXT,
            valor_limite REAL,
            PRIMARY KEY (usuario_id, categoria)
        )
    ''')
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

def atualizar_salario(username, novo_salario):
    conn = sqlite3.connect('finance.db')
    conn.execute("UPDATE usuarios SET salario = ? WHERE username = ?", (novo_salario, username))
    conn.commit()
    conn.close()

def definir_meta(username, categoria, limite):
    conn = sqlite3.connect('finance.db')
    conn.execute("INSERT OR REPLACE INTO metas VALUES (?, ?, ?)", (username, categoria, limite))
    conn.commit()
    conn.close()

def carregar_metas(username):
    conn = sqlite3.connect('finance.db')
    df = pd.read_sql("SELECT categoria, valor_limite FROM metas WHERE usuario_id = ?", conn, params=(username,))
    conn.close()
    return df

def salvar_no_banco(df, username):
    conn = sqlite3.connect('finance.db')
    df['usuario_id'] = username
    df.to_sql('transacoes', conn, if_exists='append', index=False)
    conn.close()

def carregar_do_banco(username):
    conn = sqlite3.connect('finance.db')
    # Importante: agora pegamos o ID para poder deletar
    query = "SELECT id, Data, Descricao, Valor, Categoria FROM transacoes WHERE usuario_id = ?"
    df = pd.read_sql(query, conn, params=(username,))
    conn.close()
    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])
    return df

def deletar_transacao(id_transacao):
    conn = sqlite3.connect('finance.db')
    conn.execute("DELETE FROM transacoes WHERE id = ?", (id_transacao,))
    conn.commit()
    conn.close()

def login_usuario(usuario, senha):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM usuarios WHERE username = ? AND password = ?', (usuario, hash_senha(senha)))
    res = cursor.fetchone()
    conn.close()
    return res

def cadastrar_usuario(usuario, senha):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM usuarios WHERE username = ?', (usuario,))
    if cursor.fetchone():
        conn.close()
        return False
    try:
        cursor.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (usuario, hash_senha(senha)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()