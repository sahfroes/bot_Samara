import sqlite3

DB_NAME = "usuarios.db"

def inicializar_banco():
    """Cria o arquivo de banco de dados e a tabela se ela não existir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Cria a tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            cpf TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            genero TEXT NOT NULL
        )
    """)
    
    # Lista de teste corrigida com as vírgulas nos lugares certos
    usuarios_teste = [
        ("12345678900", "Amanda Souza", "F"),
        ("98765432100", "Carlos Silva", "M"),
        ("11122233344", "Fernanda Ribeiro", "F"),
        ("04531200160", "Sarah", "F")
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO usuarios (cpf, nome, genero) 
        VALUES (?, ?, ?)
    """, usuarios_teste)
    
    conn.commit()
    conn.close()

def consultar_cadastro(cpf):
    """Busca o farmacêutico pelo CPF e retorna um dicionário ou None."""
    cpf_limpo = "".join(filter(str.isdigit, cpf))
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT nome, genero FROM usuarios WHERE cpf = ?", (cpf_limpo,))
    resultado = cursor.fetchone()
    
    conn.close()
    
    if resultado:
        return {"nome": resultado[0], "genero": resultado[1]}
    return None