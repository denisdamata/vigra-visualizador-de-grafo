from pyvis.network import Network
import streamlit as st

def build_network(nodes, edges):
    """Cria um grafo Pyvis a partir de listas de nós e arestas."""
    net = Network(height="600px", width="100%", directed=True)

    # Adicionar nós
    for node_id, label, layer in nodes:
        net.add_node(node_id, label=label, title=f"Camada {layer}")

    # Adicionar arestas
    for source, target in edges:
        net.add_edge(source, target)

    return net

def display_network(net):
    """Exibe o grafo interativo no Streamlit."""
    net_html = net.generate_html()
    st.components.v1.html(net_html, height=650)
