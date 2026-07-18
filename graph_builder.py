from pyvis.network import Network
import streamlit as st

def build_network(nodes, edges):
    """Cria um grafo Pyvis a partir de listas de nós e arestas."""

    net = Network(height="100vh", width="100%", directed=True)

    # Adicionar nós
    # nodes: list of tuples (id, label, layer, description)
    for node in nodes:
        if len(node) >= 4:
            node_id, label, layer, description = node[0], node[1], node[2], node[3]
        else:
            node_id, label, layer = node[0], node[1], node[2]
            description = None
        title_parts = [f"Camada: {layer}"]
        if description:
            title_parts.append(str(description))
        net.add_node(node_id, label=label, title="\n".join(title_parts))

    # Adicionar arestas
    # edges: list of tuples (id, source, target, description)
    for edge in edges:
        if len(edge) >= 4:
            _, source, target, edesc = edge[0], edge[1], edge[2], edge[3]
        else:
            source, target = edge[0], edge[1]
            edesc = None
        if edesc:
            net.add_edge(source, target, title=str(edesc))
        else:
            net.add_edge(source, target)

    return net

def display_network(net):
    """Exibe o grafo interativo no Streamlit."""
    net_html = net.generate_html()
    st.components.v1.html(net_html, height=650)
