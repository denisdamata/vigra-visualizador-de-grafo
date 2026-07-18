import streamlit as st
import pandas as pd
from database import (
    get_connection, add_node, add_edge, delete_node, delete_edge, delete_document,
    get_nodes, get_edges, get_all_data, update_node, update_edge, update_document,
    create_graph, list_graphs, delete_graph, graph_exists
)
from graph_builder import build_network, display_network
from utils import save_uploaded_file, get_entity_label
import os
import uuid
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Grafo Filosófico", page_icon="🦈", layout="wide")

# Conectar ao banco de dados
conn = get_connection()

# Initialize session state
if "current_graph" not in st.session_state:
    st.session_state.current_graph = 1

# ============================================
# SIDEBAR - Gerenciador de Grafos
# ============================================
with st.sidebar:
    col_header, col_settings = st.columns([4, 1])
    
    with col_header:
        st.header(f"📂 Editar Grafo #{st.session_state.current_graph}")
    
    with col_settings:
        if st.button("⚙️", key="settings_btn", help="Gerenciador de Grafos"):
            st.session_state.show_graph_settings = not st.session_state.get("show_graph_settings", False)
    
    if st.session_state.get("show_graph_settings", False):
        st.divider()
        col_menu1, col_menu2 = st.columns(2)
        
        with col_menu1:
            if st.button("➕ Novo", use_container_width=True):
                st.session_state.show_new_graph = True
        
        with col_menu2:
            if st.button("🗑️ Deletar", use_container_width=True):
                st.session_state.show_delete_graph = True
        
        # Dropdown para abrir grafo
        graphs = list_graphs(conn)
        if graphs:
            graph_names = {g[1]: g[0] for g in graphs}
            current_graph_name = next((g[1] for g in graphs if g[0] == st.session_state.current_graph), "Default")
            selected_graph_name = st.selectbox(
                "📂 Abrir Grafo",
                options=list(graph_names.keys()),
                index=list(graph_names.keys()).index(current_graph_name),
                key="graph_selector"
            )
            if selected_graph_name and st.session_state.current_graph != graph_names[selected_graph_name]:
                st.session_state.current_graph = graph_names[selected_graph_name]
                st.rerun()
        
        st.caption(f"Grafos: {len(graphs)}")
        
        # Dialog para criar novo grafo
        if st.session_state.get("show_new_graph", False):
            st.divider()
            new_graph_name = st.text_input("Nome do novo grafo", key="new_graph_input")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✓ Criar", use_container_width=True, key="create_graph_btn"):
                    if new_graph_name:
                        try:
                            new_id = create_graph(conn, new_graph_name)
                            st.session_state.current_graph = new_id
                            st.session_state.show_new_graph = False
                            st.success(f"Grafo '{new_graph_name}' criado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao criar grafo: {e}")
                    else:
                        st.warning("Digite um nome para o grafo.")
            with col2:
                if st.button("✗ Cancelar", use_container_width=True):
                    st.session_state.show_new_graph = False
        
        # Dialog para deletar grafo
        if st.session_state.get("show_delete_graph", False):
            st.divider()
            graphs = list_graphs(conn)
            if len(graphs) > 1:
                deletable_graphs = [g for g in graphs if g[0] != 1]
                if deletable_graphs:
                    graph_to_delete_name = st.selectbox(
                        "Selecionar grafo",
                        options=[g[1] for g in deletable_graphs],
                        key="delete_graph_select"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Deletar", use_container_width=True, key="confirm_delete_btn"):
                            graph_to_delete_id = next(g[0] for g in deletable_graphs if g[1] == graph_to_delete_name)
                            try:
                                delete_graph(conn, graph_to_delete_id)
                                if st.session_state.current_graph == graph_to_delete_id:
                                    st.session_state.current_graph = 1
                                st.session_state.show_delete_graph = False
                                st.success(f"Grafo '{graph_to_delete_name}' deletado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao deletar: {e}")
                    with col2:
                        if st.button("✗ Cancelar", use_container_width=True):
                            st.session_state.show_delete_graph = False
                else:
                    st.info("Apenas o grafo padrão existe.")
            else:
                st.info("Não há grafos para deletar.")
        st.divider()
    else:
        st.divider()
    
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
                    add_node(conn, label, layer, node_description or None, st.session_state.current_graph)
                    st.success(f"Nó '{label}' adicionado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

        st.divider()
        st.subheader("📋 Nós Existentes")
        nodes_df = pd.read_sql(
            "SELECT id, label, layer, description FROM nodes WHERE graph_id=? ORDER BY layer",
            conn,
            params=(st.session_state.current_graph,)
        )
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
        nodes = conn.execute(
            "SELECT id, label FROM nodes WHERE graph_id=?",
            (st.session_state.current_graph,)
        ).fetchall()
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
                            1 if directed else 0,
                            st.session_state.current_graph
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
            WHERE e.graph_id = ?
        """, conn, params=(st.session_state.current_graph,))
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
                entities = conn.execute(
                    "SELECT id, label FROM nodes WHERE graph_id=?",
                    (st.session_state.current_graph,)
                ).fetchall()
            else:
                entities = conn.execute("""
                    SELECT e.id, n1.label || ' → ' || n2.label as label
                    FROM edges e
                    JOIN nodes n1 ON e.source = n1.id
                    JOIN nodes n2 ON e.target = n2.id
                    WHERE e.graph_id = ?
                """, (st.session_state.current_graph,)).fetchall()

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
                                INSERT INTO documents (graph_id, entity_type, entity_id, filename, original_name, mime_type, description, uploaded_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (st.session_state.current_graph, entity_type, entity_options[entity], filename, uploaded_file.name, uploaded_file.type, description, datetime.now()))
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
            WHERE d.graph_id = ?
            ORDER BY d.uploaded_at DESC
        """, conn, params=(st.session_state.current_graph,))

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
nodes, edges, documents = get_all_data(conn, st.session_state.current_graph)

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
    docs_count = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE graph_id=?",
        (st.session_state.current_graph,)
    ).fetchone()[0]
    st.metric("Documentos", docs_count)

# Fechar conexão
conn.close()
