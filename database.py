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

def delete_node(conn, node_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE entity_type='node' AND entity_id=?", (node_id,))
    cursor.execute("DELETE FROM edges WHERE source=? OR target=?", (node_id, node_id))
    cursor.execute("DELETE FROM nodes WHERE id=?", (node_id,))
    conn.commit()

def delete_edge(conn, edge_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE entity_type='edge' AND entity_id=?", (edge_id,))
    cursor.execute("DELETE FROM edges WHERE id=?", (edge_id,))
    conn.commit()

def delete_document(conn, document_id):
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM documents WHERE id=?", (document_id,))
    row = cursor.fetchone()
    if row:
        filename = row[0]
        filepath = os.path.join("uploads", filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
    cursor.execute("DELETE FROM documents WHERE id=?", (document_id,))
    conn.commit()

def get_nodes(conn):
    return conn.execute("SELECT id, label, layer FROM nodes ORDER BY layer").fetchall()

def get_edges(conn):
    return conn.execute("SELECT source, target FROM edges").fetchall()

def get_all_data(conn):
    """Retorna todos os dados (nós e arestas) para construir o grafo."""
    return get_nodes(conn), get_edges(conn)
