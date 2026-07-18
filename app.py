import streamlit as st
import pandas as pd
from database import get_connection, add_node, add_edge, get_nodes, get_edges, get_all_data
from graph_builder import build_network, display_network
from utils import save_uploaded_file, get_entity_label
import os
import uuid
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Grafo Filosófico", layout="wide")
st.title("🌌 Grafo Filosófico Universal")

# Conectar ao banco de dados
conn = get_connection()

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.header("📂 Gerenciar Grafo")
    tab1, tab2, tab3 = st.tabs(["➕ Nós", "🔗 Arestas", "📄 Documentos"])

    # [TABS 1 e 2 ... (código existente, mas usando as funções do database.py)]
    # Exemplo para adicionar nó:
    with tab1:
        st.subheader("Adicionar Nó")
        label = st.text_input("Rótulo", key="new_node_label")
        layer = st.number_input("Camada", min_value=0, step=1, key="new_node_layer")
        if st.button("➕ Adicionar Nó", use_container_width=True):
            if label:
                try:
                    add_node(conn, label, layer)
                    st.success(f"Nó '{label}' adicionado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
    with tab2:
        st.subheader("Adicionar Aresta")
        nodes = conn.execute("SELECT id, label FROM nodes").fetchall()
        node_options = {f"{label} (ID: {id})": id for id, label in nodes}

        if len(nodes) < 2:
            st.warning("Adicione pelo menos dois nós antes de criar arestas.")
        else:
            source = st.selectbox("Origem", options=list(node_options.keys()), key="source_select")
            target = st.selectbox("Destino", options=list(node_options.keys()), key="target_select")
            if st.button("➕ Adicionar Aresta", use_container_width=True):
                if source and target:
                    try:
                        conn.execute("INSERT INTO edges (source, target) VALUES (?, ?)",
                                    (node_options[source], node_options[target]))
                        conn.commit()
                        st.success("Aresta adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        st.divider()
        st.subheader("📋 Arestas Existentes")
        edges_df = pd.read_sql("""
            SELECT e.id, n1.label as source_label, n2.label as target_label
            FROM edges e
            JOIN nodes n1 ON e.source = n1.id
            JOIN nodes n2 ON e.target = n2.id
        """, conn)
        st.dataframe(edges_df, use_container_width=True)

    with tab3:
        st.subheader("📄 Anexar Documento")
        uploaded_file = st.file_uploader("Escolher arquivo", type=["pdf", "png", "jpg", "jpeg", "txt", "md", "csv"])

        if uploaded_file:
            entity_type = st.selectbox("Vincular a", ["node", "edge"])

            if entity_type == "node":
                entities = conn.execute("SELECT id, label FROM nodes").fetchall()
            else:
                entities = conn.execute("""
                    SELECT e.id, n1.label || ' → ' || n2.label as label
                    FROM edges e
                    JOIN nodes n1 ON e.source = n1.id
                    JOIN nodes n2 ON e.target = n2.id
                """).fetchall()

            if entities:
                entity_options = {f"{label} (ID: {id})": id for id, label in entities}
                entity = st.selectbox("Selecionar entidade", options=list(entity_options.keys()))
                description = st.text_area("Descrição (opcional)")

                if st.button("💾 Salvar Documento", use_container_width=True):
                    if entity:
                        try:
                            # Salvar arquivo
                            ext = uploaded_file.name.split(".")[-1]
                            filename = f"{uuid.uuid4()}.{ext}"
                            filepath = os.path.join("uploads", filename)
                            with open(filepath, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Salvar no banco
                            conn.execute("""
                                INSERT INTO documents (entity_type, entity_id, filename, original_name, mime_type, description, uploaded_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (entity_type, entity_options[entity], filename, uploaded_file.name, uploaded_file.type, description, datetime.now()))
                            conn.commit()
                            st.success(f"Documento '{uploaded_file.name}' anexado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
            else:
                st.info("Crie pelo menos um nó ou aresta antes de anexar documentos.")

        st.divider()
        st.subheader("📋 Documentos Anexados")
        docs = pd.read_sql("""
            SELECT d.id, d.entity_type, d.entity_id, d.original_name, d.description,
                n.label as node_label,
                e.source || ' → ' || e.target as edge_label
            FROM documents d
            LEFT JOIN nodes n ON d.entity_type='node' AND d.entity_id=n.id
            LEFT JOIN edges e ON d.entity_type='edge' AND d.entity_id=e.id
            ORDER BY d.uploaded_at DESC
        """, conn)

        if not docs.empty:
            for _, doc in docs.iterrows():
                entity_label = doc['node_label'] if doc['entity_type'] == 'node' else doc['edge_label']
                with st.expander(f"📎 {doc['original_name']} ({entity_label})"):
                    st.write(f"**Descrição:** {doc['description'] or 'Sem descrição'}")
                    if st.button(f"🔗 Abrir", key=f"open_{doc['id']}"):
                        # Gera um link para o arquivo
                        st.markdown(f"[Abrir arquivo](uploads/{doc['filename']})", unsafe_allow_html=True)
        else:
            st.info("Nenhum documento anexado.")

# ============================================
# ÁREA PRINCIPAL: Visualização do grafo
# ============================================
st.subheader("📊 Visualização do Grafo")

# Buscar dados
nodes, edges = get_all_data(conn)

if not nodes:
    st.info("Adicione seus primeiros nós e arestas na barra lateral para começar.")
else:
    # Construir e exibir o grafo
    net = build_network(nodes, edges)
    display_network(net)

# Estatísticas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Nós", len(nodes))
with col2:
    st.metric("Arestas", len(edges))
with col3:
    docs_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    st.metric("Documentos", docs_count)

# Fechar conexão
conn.close()
