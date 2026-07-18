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

# Page configuration
st.set_page_config(page_title="Vigra - Graph Visualizer", page_icon="🕸️", layout="wide")

# Custom styling for better text visibility
st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            color: #111 !important;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
            font-weight: 700 !important;
            letter-spacing: 0.02em !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
        }
        .stApp p, .stApp label, .stApp div, .stApp span {
            font-weight: 600 !important;
            line-height: 1.5 !important;
        }
        .stButton>button {
            font-weight: 700 !important;
            letter-spacing: 0.02em !important;
        }
        .stMarkdown, .stText, .stSelectbox, .stTextArea, .stNumberInput {
            color: #111 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Connect to the database
conn = get_connection()

# Initialize session state
if "current_graph" not in st.session_state:
    st.session_state.current_graph = 1

# ============================================
# SIDEBAR - Graph Manager
# ============================================
with st.sidebar:
    col_header, col_settings = st.columns([4, 1])
    
    with col_header:
        st.header(f"📂 Edit Graph #{st.session_state.current_graph}")
    
    with col_settings:
        if st.button("⚙️", key="settings_btn", help="Graph manager"):
            st.session_state.show_graph_settings = not st.session_state.get("show_graph_settings", False)
    
    if st.session_state.get("show_graph_settings", False):
        st.divider()
        col_menu1, col_menu2 = st.columns(2)
        
        with col_menu1:
            if st.button("➕ New", use_container_width=True):
                st.session_state.show_new_graph = True
        
        with col_menu2:
            if st.button("🗑️ Delete", use_container_width=True):
                st.session_state.show_delete_graph = True
        
        # Dropdown to open graph
        graphs = list_graphs(conn)
        if graphs:
            graph_names = {g[1]: g[0] for g in graphs}
            current_graph_name = next((g[1] for g in graphs if g[0] == st.session_state.current_graph), "Default")
            selected_graph_name = st.selectbox(
                "📂 Open Graph",
                options=list(graph_names.keys()),
                index=list(graph_names.keys()).index(current_graph_name),
                key="graph_selector"
            )
            if selected_graph_name and st.session_state.current_graph != graph_names[selected_graph_name]:
                st.session_state.current_graph = graph_names[selected_graph_name]
                st.rerun()
        
        st.caption(f"Graphs: {len(graphs)}")
        
        # Dialog to create a new graph
        if st.session_state.get("show_new_graph", False):
            st.divider()
            new_graph_name = st.text_input("New graph name", key="new_graph_input")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✓ Create", use_container_width=True, key="create_graph_btn"):
                    if new_graph_name:
                        try:
                            new_id = create_graph(conn, new_graph_name)
                            st.session_state.current_graph = new_id
                            st.session_state.show_new_graph = False
                            st.success(f"Graph '{new_graph_name}' created!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating graph: {e}")
                    else:
                        st.warning("Enter a name for the graph.")
            with col2:
                if st.button("✗ Cancel", use_container_width=True):
                    st.session_state.show_new_graph = False
        
        # Dialog to delete graph
        if st.session_state.get("show_delete_graph", False):
            st.divider()
            graphs = list_graphs(conn)
            if len(graphs) > 1:
                deletable_graphs = [g for g in graphs if g[0] != 1]
                if deletable_graphs:
                    graph_to_delete_name = st.selectbox(
                        "Select graph",
                        options=[g[1] for g in deletable_graphs],
                        key="delete_graph_select"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Delete", use_container_width=True, key="confirm_delete_btn"):
                            graph_to_delete_id = next(g[0] for g in deletable_graphs if g[1] == graph_to_delete_name)
                            try:
                                delete_graph(conn, graph_to_delete_id)
                                if st.session_state.current_graph == graph_to_delete_id:
                                    st.session_state.current_graph = 1
                                st.session_state.show_delete_graph = False
                                st.success(f"Graph '{graph_to_delete_name}' deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting graph: {e}")
                    with col2:
                        if st.button("✗ Cancel", use_container_width=True):
                            st.session_state.show_delete_graph = False
                else:
                    st.info("Only the default graph exists.")
            else:
                st.info("There are no graphs to delete.")
        st.divider()
    else:
        st.divider()
    
    tab1, tab2, tab3 = st.tabs(["➕ Nodes", "🔗 Edges", "📄 Documents"])

    # [TABS 1 e 2 ... (código existente, mas usando as funções do database.py)]
    # Example to add a node:
    with tab1:
        st.subheader("Add Node")
        label = st.text_input("Label", key="new_node_label")
        layer = st.number_input("Layer", min_value=0, step=1, key="new_node_layer")
        node_description = st.text_area("Description (optional)", key="new_node_description", height=80)
        if st.button("➕ Add Node", use_container_width=True):
            if label:
                try:
                    add_node(conn, label, layer, node_description or None, st.session_state.current_graph)
                    st.success(f"Node '{label}' added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.divider()
        st.subheader("📋 Existing Nodes")
        nodes_df = pd.read_sql(
            "SELECT id, label, layer, description FROM nodes WHERE graph_id=? ORDER BY layer",
            conn,
            params=(st.session_state.current_graph,)
        )
        if not nodes_df.empty:
            st.dataframe(nodes_df, use_container_width=True)
            
            st.subheader("✏️ Edit Node")
            node_options = [
                (f"{row['label']} (ID: {row['id']}, Layer: {row['layer']})", row['id'])
                for _, row in nodes_df.iterrows()
            ]
            edit_node_select = st.selectbox(
                "Select node to edit",
                options=[option[1] for option in node_options],
                format_func=lambda node_id, node_options=node_options: next(label for label, id in node_options if id == node_id),
                key="edit_node_select"
            )
            if edit_node_select:
                node_to_edit = nodes_df[nodes_df['id'] == edit_node_select].iloc[0]
                new_label = st.text_input("Label", value=node_to_edit['label'], key="edit_node_label")
                new_layer = st.number_input("Layer", value=node_to_edit['layer'], min_value=0, step=1, key="edit_node_layer")
                new_description = st.text_area("Description", value=node_to_edit['description'] or "", key="edit_node_description", height=80)
                if st.button("💾 Save changes", use_container_width=True, key="save_node_edit"):
                    try:
                        update_node(conn, edit_node_select, new_label, new_layer, new_description or None)
                        st.success("Node updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating: {e}")
            
            st.divider()
            selected_node_ids = st.multiselect(
                "Select nodes to delete",
                options=[option[1] for option in node_options],
                format_func=lambda node_id, node_options=node_options: next(label for label, id in node_options if id == node_id),
            )
            if st.button("🗑️ Delete selected nodes", use_container_width=True):
                if selected_node_ids:
                    try:
                        for node_id in selected_node_ids:
                            delete_node(conn, int(node_id))
                        st.success(f"{len(selected_node_ids)} node(s) deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting nodes: {e}")
                else:
                    st.warning("Select at least one node to delete.")
        else:
            st.info("No nodes registered yet.")

    with tab2:
        st.subheader("Add Edge")
        nodes = conn.execute(
            "SELECT id, label FROM nodes WHERE graph_id=?",
            (st.session_state.current_graph,)
        ).fetchall()
        node_options = {f"{label} (ID: {id})": id for id, label in nodes}

        if len(nodes) < 2:
            st.warning("Add at least two nodes before creating edges.")
        else:
            source = st.selectbox("Source", options=list(node_options.keys()), key="source_select")
            target = st.selectbox("Target", options=list(node_options.keys()), key="target_select")
            directed = st.checkbox("Directed", value=True, key="new_edge_directed")
            edge_description = st.text_area("Edge description (optional)", key="new_edge_description", height=80)
            if st.button("➕ Add Edge", use_container_width=True):
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
                        st.success("Edge added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.divider()
        st.subheader("📋 Existing Edges")
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
            
            st.subheader("✏️ Edit Edge")
            edit_edge_select = st.selectbox(
                "Select edge to edit",
                options=[option[1] for option in edge_options],
                format_func=lambda edge_id, edge_options=edge_options: next(label for label, id in edge_options if id == edge_id),
                key="edit_edge_select"
            )
            if edit_edge_select:
                edge_to_edit = conn.execute(
                    "SELECT description, directed FROM edges WHERE id=?",
                    (edit_edge_select,)
                ).fetchone()
                new_description = st.text_area("Description", value=edge_to_edit[0] or "", key="edit_edge_description", height=80)
                new_directed = st.checkbox("Directed", value=bool(edge_to_edit[1]), key="edit_edge_directed")
                if st.button("💾 Save changes", use_container_width=True, key="save_edge_edit"):
                    try:
                        update_edge(conn, edit_edge_select, new_description or None, 1 if new_directed else 0)
                        st.success("Edge updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating: {e}")
            
            st.divider()
            selected_edge_ids = st.multiselect(
                "Select edges to delete",
                options=[option[1] for option in edge_options],
                format_func=lambda edge_id, edge_options=edge_options: next(label for label, id in edge_options if id == edge_id),
            )
            if st.button("🗑️ Delete selected edges", use_container_width=True):
                if selected_edge_ids:
                    try:
                        for edge_id in selected_edge_ids:
                            delete_edge(conn, int(edge_id))
                        st.success(f"{len(selected_edge_ids)} edge(s) deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting edges: {e}")
                else:
                    st.warning("Select at least one edge to delete.")
        else:
            st.info("No edges registered yet.")

    with tab3:
        st.subheader("📄 Attach Document")
        uploaded_file = st.file_uploader("Choose file", type=["pdf", "png", "jpg", "jpeg", "txt", "md", "csv"])

        if uploaded_file:
            entity_type = st.selectbox("Attach to", ["node", "edge"])

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
                entity = st.selectbox("Select entity", options=list(entity_options.keys()))
                description = st.text_area("Description (optional)")

                if st.button("💾 Save Document", use_container_width=True):
                    if entity:
                        try:
                            # Save file
                            ext = uploaded_file.name.split(".")[-1]
                            filename = f"{uuid.uuid4()}.{ext}"
                            filepath = os.path.join("uploads", filename)
                            with open(filepath, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            # Save to database
                            conn.execute("""
                                INSERT INTO documents (graph_id, entity_type, entity_id, filename, original_name, mime_type, description, uploaded_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (st.session_state.current_graph, entity_type, entity_options[entity], filename, uploaded_file.name, uploaded_file.type, description, datetime.now()))
                            conn.commit()
                            st.success(f"Document '{uploaded_file.name}' attached!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving: {e}")
            else:
                st.info("Create at least one node or edge before attaching documents.")

        st.divider()
        st.subheader("📋 Attached Documents")
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
            st.subheader("✏️ Edit Document")
            doc_options = [
                (f"{doc['original_name']}", doc['id'])
                for _, doc in docs.iterrows()
            ]
            edit_doc_select = st.selectbox(
                "Select document to edit",
                options=[option[1] for option in doc_options],
                format_func=lambda doc_id, doc_options=doc_options: next(label for label, id in doc_options if id == doc_id),
                key="edit_doc_select"
            )
            if edit_doc_select:
                doc_to_edit = docs[docs['id'] == edit_doc_select].iloc[0]
                new_description = st.text_area("Description", value=doc_to_edit['description'] or "", key="edit_doc_description", height=80)
                if st.button("💾 Save changes", use_container_width=True, key="save_doc_edit"):
                    try:
                        update_document(conn, edit_doc_select, new_description or None)
                        st.success("Document updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating: {e}")
            
            st.divider()
            for _, doc in docs.iterrows():
                entity_label = doc['node_label'] if doc['entity_type'] == 'node' else doc['edge_label']
                with st.expander(f"📎 {doc['original_name']} ({entity_label})"):
                    st.write(f"**Description:** {doc['description'] or 'No description'}")
                    cols = st.columns([1, 1])
                    if cols[0].button(f"🔗 Open", key=f"open_{doc['id']}"):
                        st.markdown(f"[Open file](uploads/{doc['filename']})", unsafe_allow_html=True)
                    if cols[1].button(f"🗑️ Delete document", key=f"delete_doc_{doc['id']}"):
                        try:
                            delete_document(conn, doc['id'])
                            st.success(f"Document '{doc['original_name']}' deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting document: {e}")
        else:
            st.info("No attached documents.")

# ============================================
# MAIN AREA: Graph visualization
# ============================================

# Fetch data
nodes, edges, documents = get_all_data(conn, st.session_state.current_graph)

if not nodes:
    st.info("Add your first nodes and edges in the sidebar to start.")
else:
    # Build and display the graph
    net = build_network(nodes, edges, documents)
    display_network(net)

# Statistics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Nodes", len(nodes))
with col2:
    st.metric("Edges", len(edges))
with col3:
    docs_count = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE graph_id=?",
        (st.session_state.current_graph,)
    ).fetchone()[0]
    st.metric("Documents", docs_count)

# Close connection
conn.close()
