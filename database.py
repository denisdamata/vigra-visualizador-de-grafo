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
    CREATE TABLE IF NOT EXISTS graphs (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY,
        graph_id INTEGER,
        label TEXT,
        layer INTEGER,
        description TEXT,
        FOREIGN KEY (graph_id) REFERENCES graphs(id),
        UNIQUE(graph_id, label)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY,
        graph_id INTEGER,
        source INTEGER,
        target INTEGER,
        description TEXT,
        directed INTEGER DEFAULT 1,
        FOREIGN KEY (graph_id) REFERENCES graphs(id),
        FOREIGN KEY (source) REFERENCES nodes(id),
        FOREIGN KEY (target) REFERENCES nodes(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY,
        graph_id INTEGER,
        entity_type TEXT CHECK(entity_type IN ('node', 'edge')),
        entity_id INTEGER,
        filename TEXT,
        original_name TEXT,
        mime_type TEXT,
        description TEXT,
        uploaded_at TIMESTAMP,
        FOREIGN KEY (graph_id) REFERENCES graphs(id)
    )
    """)
    conn.commit()
    
    # Migrate existing data if needed
    cols_n = [r[1] for r in conn.execute("PRAGMA table_info(nodes)").fetchall()]
    if 'graph_id' not in cols_n:
        cursor.execute("ALTER TABLE nodes ADD COLUMN graph_id INTEGER DEFAULT 1")
        cursor.execute("UPDATE nodes SET graph_id=1 WHERE graph_id IS NULL")
    if 'description' not in cols_n:
        cursor.execute("ALTER TABLE nodes ADD COLUMN description TEXT")
    
    cols_e = [r[1] for r in conn.execute("PRAGMA table_info(edges)").fetchall()]
    if 'graph_id' not in cols_e:
        cursor.execute("ALTER TABLE edges ADD COLUMN graph_id INTEGER DEFAULT 1")
        cursor.execute("UPDATE edges SET graph_id=1 WHERE graph_id IS NULL")
    if 'description' not in cols_e:
        cursor.execute("ALTER TABLE edges ADD COLUMN description TEXT")
    if 'directed' not in cols_e:
        cursor.execute("ALTER TABLE edges ADD COLUMN directed INTEGER DEFAULT 1")
        cursor.execute("UPDATE edges SET directed=1 WHERE directed IS NULL")
    
    cols_d = [r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()]
    if 'graph_id' not in cols_d:
        cursor.execute("ALTER TABLE documents ADD COLUMN graph_id INTEGER DEFAULT 1")
        cursor.execute("UPDATE documents SET graph_id=1 WHERE graph_id IS NULL")
    
    conn.commit()
    
    # Ensure default graph exists
    cursor.execute("INSERT OR IGNORE INTO graphs (id, name, created_at, updated_at) VALUES (1, 'Default', datetime('now'), datetime('now'))")
    conn.commit()

def add_node(conn, label, layer, description=None, graph_id=1):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO nodes (graph_id, label, layer, description) VALUES (?, ?, ?, ?)",
        (graph_id, label, layer, description)
    )
    conn.commit()
    return cursor.lastrowid

def add_edge(conn, source, target, description=None, directed=1, graph_id=1):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO edges (graph_id, source, target, description, directed) VALUES (?, ?, ?, ?, ?)",
        (graph_id, source, target, description, directed)
    )
    conn.commit()
    return cursor.lastrowid

def update_node(conn, node_id, label, layer, description=None):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE nodes SET label=?, layer=?, description=? WHERE id=?",
        (label, layer, description, node_id)
    )
    conn.commit()

def update_edge(conn, edge_id, description=None, directed=1):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE edges SET description=?, directed=? WHERE id=?",
        (description, directed, edge_id)
    )
    conn.commit()

def update_document(conn, document_id, description=None):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET description=? WHERE id=?",
        (description, document_id)
    )
    conn.commit()

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

def get_nodes(conn, graph_id=1):
    return conn.execute("SELECT id, label, layer, description FROM nodes WHERE graph_id=? ORDER BY layer", (graph_id,)).fetchall()

def get_edges(conn, graph_id=1):
    return conn.execute("SELECT id, source, target, description, directed FROM edges WHERE graph_id=?", (graph_id,)).fetchall()

def get_documents(conn, graph_id=1):
    return conn.execute(
        "SELECT entity_type, entity_id, original_name FROM documents WHERE graph_id=?",
        (graph_id,)
    ).fetchall()

def get_all_data(conn, graph_id=1):
    """Retorna todos os dados (nós, arestas e documentos) para construir o grafo."""
    return get_nodes(conn, graph_id), get_edges(conn, graph_id), get_documents(conn, graph_id)

def create_graph(conn, name):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO graphs (name, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))",
        (name,)
    )
    conn.commit()
    return cursor.lastrowid

def list_graphs(conn):
    return conn.execute("SELECT id, name FROM graphs ORDER BY name").fetchall()

def delete_graph(conn, graph_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE graph_id=?", (graph_id,))
    cursor.execute("DELETE FROM edges WHERE graph_id=?", (graph_id,))
    cursor.execute("DELETE FROM nodes WHERE graph_id=?", (graph_id,))
    cursor.execute("DELETE FROM graphs WHERE id=?", (graph_id,))
    conn.commit()

def graph_exists(conn, graph_id):
    result = conn.execute("SELECT id FROM graphs WHERE id=?", (graph_id,)).fetchone()
    return result is not None
