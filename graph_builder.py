from pyvis.network import Network
import streamlit as st


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def interpolate_color(color_a, color_b, t):
    return tuple(
        int(color_a[i] + (color_b[i] - color_a[i]) * t)
        for i in range(3)
    )


def build_network(nodes, edges):
    """Cria um grafo Pyvis a partir de listas de nós e arestas."""

    net = Network(height="100vh", width="100%", directed=True)

    # Determinar cores de nós com base na camada
    start_color = hex_to_rgb("#0000ff")  # azul
    end_color = hex_to_rgb("#ff0000")  # vermelho

    node_colors = {}
    layers = [node[2] for node in nodes if len(node) >= 3]
    min_layer = min(layers) if layers else 0
    max_layer = max(layers) if layers else 0
    layer_span = max_layer - min_layer if max_layer != min_layer else 1

    for node in nodes:
        if len(node) >= 4:
            node_id, label, layer, description = node[0], node[1], node[2], node[3]
        else:
            node_id, label, layer = node[0], node[1], node[2]
            description = None

        t = (layer - min_layer) / layer_span
        rgb_color = interpolate_color(start_color, end_color, t)
        color_hex = rgb_to_hex(rgb_color)
        node_colors[node_id] = color_hex

        title_parts = [f"Camada: {layer}"]
        if description:
            title_parts.append(str(description))

        net.add_node(node_id, label=label, title="\n".join(title_parts), color=color_hex)

    # Adicionar arestas com cor intermediária entre as extremidades
    for edge in edges:
        if len(edge) >= 4:
            _, source, target, edesc = edge[0], edge[1], edge[2], edge[3]
        else:
            source, target = edge[0], edge[1]
            edesc = None

        source_color = hex_to_rgb(node_colors.get(source, "#888888"))
        target_color = hex_to_rgb(node_colors.get(target, "#888888"))
        edge_rgb = interpolate_color(source_color, target_color, 0.5)
        edge_color = rgb_to_hex(edge_rgb)

        if edesc:
            net.add_edge(source, target, title=str(edesc), color=edge_color)
        else:
            net.add_edge(source, target, color=edge_color)

    return net


def display_network(net):
    """Exibe o grafo interativo no Streamlit."""
    net_html = net.generate_html()
    st.components.v1.html(net_html, height=650)
