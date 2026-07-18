import sqlite3
import os

DB_PATH = "database/graph.db"

def get_connection():
    """Retorna uma conexão com o banco de dados e cria a estrutura se necessário."""
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    _create_tables(conn)
    return conn

def _create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY,
        label TEXT UNIQUE,
        layer INTEGER
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY,
        source INTEGER,
        target INTEGER,
        FOREIGN KEY (source) REFERENCES nodes(id),
        FOREIGN KEY (target) REFERENCES nodes(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        entity_type TEXT CHECK(entity_type IN ('node', 'edge')),
        entity_id INTEGER,
        filename TEXT,
        original_name TEXT,
        mime_type TEXT,
        description TEXT,
        uploaded_at TIMESTAMP
    )
    """)
    conn.commit()

def add_node(conn, label, layer):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO nodes (label, layer) VALUES (?, ?)", (label, layer))
    conn.commit()
    return cursor.lastrowid

def add_edge(conn, source, target):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edges (source, target) VALUES (?, ?)", (source, target))
    conn.commit()
    return cursor.lastrowid

def get_nodes(conn):
    return conn.execute("SELECT id, label, layer FROM nodes ORDER BY layer").fetchall()

def get_edges(conn):
    return conn.execute("SELECT source, target FROM edges").fetchall()

def get_all_data(conn):
    """Retorna todos os dados (nós e arestas) para construir o grafo."""
    return get_nodes(conn), get_edges(conn)
