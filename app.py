import streamlit as st
import pandas as pd
from database import get_connection, add_node, add_edge, delete_node, delete_edge, delete_document, get_nodes, get_edges, get_all_data, update_node, update_edge, update_document
from graph_builder import build_network, display_network
from utils import save_uploaded_file, get_entity_label
import os
import uuid
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Grafo Filosófico", page_icon="🦈", layout="wide")
# st.title("🌌 Grafo Filosófico Universal")

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
        node_description = st.text_area("Descrição (opcional)", key="new_node_description", height=80)
        if st.button("➕ Adicionar Nó", use_container_width=True):
            if label:
                try:
                    add_node(conn, label, layer, node_description or None)
                    st.success(f"Nó '{label}' adicionado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.divider()
        st.subheader("📋 Nós Existentes")
        nodes_df = pd.read_sql("SELECT id, label, layer, description FROM nodes ORDER BY layer", conn)
        if not nodes_df.empty:
            st.dataframe(nodes_df, use_container_width=True)
            
            st.subheader("✏️ Editar Nó")
            node_options = [
                (f"{row['label']} (ID: {row['id']}, Camada: {row['layer']})", row['id'])
                for _, row in nodes_df.iterrows()
            ]
            edit_node_select = st.selectbox(
                "Selecionar nó para editar",
                options=[option[1] for option in node_options],
                format_func=lambda node_id, node_options=node_options: next(label for label, id in node_options if id == node_id),
                key="edit_node_select"
            )
            if edit_node_select:
                node_to_edit = nodes_df[nodes_df['id'] == edit_node_select].iloc[0]
                new_label = st.text_input("Rótulo", value=node_to_edit['label'], key="edit_node_label")
                new_layer = st.number_input("Camada", value=node_to_edit['layer'], min_value=0, step=1, key="edit_node_layer")
                new_description = st.text_area("Descrição", value=node_to_edit['description'] or "", key="edit_node_description", height=80)
                if st.button("💾 Salvar alterações", use_container_width=True, key="save_node_edit"):
                    try:
                        update_node(conn, edit_node_select, new_label, new_layer, new_description or None)
                        st.success("Nó atualizado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")
            
            st.divider()
            selected_node_ids = st.multiselect(
                "Selecionar nós para excluir",
                options=[option[1] for option in node_options],
                format_func=lambda node_id, node_options=node_options: next(label for label, id in node_options if id == node_id),
            )
            if st.button("🗑️ Excluir nós selecionados", use_container_width=True):
                if selected_node_ids:
                    try:
                        for node_id in selected_node_ids:
                            delete_node(conn, int(node_id))
                        st.success(f"{len(selected_node_ids)} nó(s) excluído(s).")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir nós: {e}")
                else:
                    st.warning("Selecione pelo menos um nó para excluir.")
        else:
            st.info("Nenhum nó cadastrado ainda.")

    with tab2:
        st.subheader("Adicionar Aresta")
        nodes = conn.execute("SELECT id, label FROM nodes").fetchall()
        node_options = {f"{label} (ID: {id})": id for id, label in nodes}

        if len(nodes) < 2:
            st.warning("Adicione pelo menos dois nós antes de criar arestas.")
        else:
            source = st.selectbox("Origem", options=list(node_options.keys()), key="source_select")
            target = st.selectbox("Destino", options=list(node_options.keys()), key="target_select")
            directed = st.checkbox("Direcional", value=True, key="new_edge_directed")
            edge_description = st.text_area("Descrição da aresta (opcional)", key="new_edge_description", height=80)
            if st.button("➕ Adicionar Aresta", use_container_width=True):
                if source and target:
                    try:
                        add_edge(
                            conn,
                            node_options[source],
                            node_options[target],
                            edge_description or None,
                            1 if directed else 0
                        )
                        st.success("Aresta adicionada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        st.divider()
        st.subheader("📋 Arestas Existentes")
        edges_df = pd.read_sql("""
            SELECT e.id, n1.label as source_label, n2.label as target_label, e.directed
            FROM edges e
            JOIN nodes n1 ON e.source = n1.id
            JOIN nodes n2 ON e.target = n2.id
        """, conn)
        if not edges_df.empty:
            st.dataframe(edges_df, use_container_width=True)
            edge_options = [
                (
                    f"{row['source_label']} {'→' if row['directed'] else '--'} {row['target_label']} (ID: {row['id']})",
                    row['id']
                )
                for _, row in edges_df.iterrows()
            ]
            
            st.subheader("✏️ Editar Aresta")
            edit_edge_select = st.selectbox(
                "Selecionar aresta para editar",
                options=[option[1] for option in edge_options],
                format_func=lambda edge_id, edge_options=edge_options: next(label for label, id in edge_options if id == edge_id),
                key="edit_edge_select"
            )
            if edit_edge_select:
                edge_to_edit = conn.execute(
                    "SELECT description, directed FROM edges WHERE id=?",
                    (edit_edge_select,)
                ).fetchone()
                new_description = st.text_area("Descrição", value=edge_to_edit[0] or "", key="edit_edge_description", height=80)
                new_directed = st.checkbox("Direcional", value=bool(edge_to_edit[1]), key="edit_edge_directed")
                if st.button("💾 Salvar alterações", use_container_width=True, key="save_edge_edit"):
                    try:
                        update_edge(conn, edit_edge_select, new_description or None, 1 if new_directed else 0)
                        st.success("Aresta atualizada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")
            
            st.divider()
            selected_edge_ids = st.multiselect(
                "Selecionar arestas para excluir",
                options=[option[1] for option in edge_options],
                format_func=lambda edge_id, edge_options=edge_options: next(label for label, id in edge_options if id == edge_id),
            )
            if st.button("🗑️ Excluir arestas selecionadas", use_container_width=True):
                if selected_edge_ids:
                    try:
                        for edge_id in selected_edge_ids:
                            delete_edge(conn, int(edge_id))
                        st.success(f"{len(selected_edge_ids)} aresta(s) excluída(s).")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir arestas: {e}")
                else:
                    st.warning("Selecione pelo menos uma aresta para excluir.")
        else:
            st.info("Nenhuma aresta cadastrada ainda.")

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
            SELECT d.id, d.entity_type, d.entity_id, d.filename, d.original_name, d.description,
                n.label as node_label,
                e.source || ' → ' || e.target as edge_label
            FROM documents d
            LEFT JOIN nodes n ON d.entity_type='node' AND d.entity_id=n.id
            LEFT JOIN edges e ON d.entity_type='edge' AND d.entity_id=e.id
            ORDER BY d.uploaded_at DESC
        """, conn)

        if not docs.empty:
            st.subheader("✏️ Editar Documento")
            doc_options = [
                (f"{doc['original_name']}", doc['id'])
                for _, doc in docs.iterrows()
            ]
            edit_doc_select = st.selectbox(
                "Selecionar documento para editar",
                options=[option[1] for option in doc_options],
                format_func=lambda doc_id, doc_options=doc_options: next(label for label, id in doc_options if id == doc_id),
                key="edit_doc_select"
            )
            if edit_doc_select:
                doc_to_edit = docs[docs['id'] == edit_doc_select].iloc[0]
                new_description = st.text_area("Descrição", value=doc_to_edit['description'] or "", key="edit_doc_description", height=80)
                if st.button("💾 Salvar alterações", use_container_width=True, key="save_doc_edit"):
                    try:
                        update_document(conn, edit_doc_select, new_description or None)
                        st.success("Documento atualizado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")
            
            st.divider()
            for _, doc in docs.iterrows():
                entity_label = doc['node_label'] if doc['entity_type'] == 'node' else doc['edge_label']
                with st.expander(f"📎 {doc['original_name']} ({entity_label})"):
                    st.write(f"**Descrição:** {doc['description'] or 'Sem descrição'}")
                    cols = st.columns([1, 1])
                    if cols[0].button(f"🔗 Abrir", key=f"open_{doc['id']}"):
                        st.markdown(f"[Abrir arquivo](uploads/{doc['filename']})", unsafe_allow_html=True)
                    if cols[1].button(f"🗑️ Excluir documento", key=f"delete_doc_{doc['id']}"):
                        try:
                            delete_document(conn, doc['id'])
                            st.success(f"Documento '{doc['original_name']}' excluído.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir documento: {e}")
        else:
            st.info("Nenhum documento anexado.")

# ============================================
# ÁREA PRINCIPAL: Visualização do grafo
# ============================================

# Buscar dados
nodes, edges, documents = get_all_data(conn)

if not nodes:
    st.info("Adicione seus primeiros nós e arestas na barra lateral para começar.")
else:
    # Construir e exibir o grafo
    net = build_network(nodes, edges, documents)
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
