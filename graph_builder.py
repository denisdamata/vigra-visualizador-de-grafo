from collections import defaultdict

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


def build_network(nodes, edges, documents=None):
    """Build a Pyvis graph from lists of nodes, edges, and documents."""

    net = Network(height="100vh", width="100%", directed=False)

    document_map = {
        'node': defaultdict(list),
        'edge': defaultdict(list)
    }
    for entity_type, entity_id, original_name in documents or []:
        document_map[entity_type][entity_id].append(original_name)

    # Determine node colors based on layer
    start_color = hex_to_rgb("#0000ff")  # blue
    end_color = hex_to_rgb("#ff0000")  # red

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

        title_parts = [f"Layer: {layer}"]
        if description:
            title_parts.append(str(description))

        if document_map['node'].get(node_id):
            title_parts.append("Documents:")
            title_parts.extend(f"- {name}" for name in document_map['node'][node_id])

        net.add_node(
            node_id,
            label=label,
            title="\n".join(title_parts),
            color=color_hex,
            size=24,
            borderWidth=2,
            font={
                "size": 18,
                "face": "Arial",
                "color": "#111111",
                "strokeWidth": 1,
                "strokeColor": "#ffffff"
            }
        )

    # Add edges with an intermediate color based on the endpoints
    for edge in edges:
        if len(edge) >= 5:
            edge_id, source, target, edesc, directed = edge[0], edge[1], edge[2], edge[3], edge[4]
        elif len(edge) == 4:
            edge_id, source, target, edesc = edge[0], edge[1], edge[2], edge[3]
            directed = 1
        else:
            edge_id, source, target = edge[0], edge[1], edge[2]
            edesc = None
            directed = 1

        source_color = hex_to_rgb(node_colors.get(source, "#888888"))
        target_color = hex_to_rgb(node_colors.get(target, "#888888"))
        edge_rgb = interpolate_color(source_color, target_color, 0.5)
        edge_color = rgb_to_hex(edge_rgb)

        edge_title_parts = []
        if edesc:
            edge_title_parts.append(str(edesc))

        if document_map['edge'].get(edge_id):
            edge_title_parts.append("Documents:")
            edge_title_parts.extend(f"- {name}" for name in document_map['edge'][edge_id])

        title = "\n".join(edge_title_parts) if edge_title_parts else None
        if directed:
            net.add_edge(source, target, title=title, color=edge_color, arrows="to")
        else:
            net.add_edge(source, target, title=title, color=edge_color)

    return net


def display_network(net):
    """Display the interactive graph in Streamlit."""
    net_html = net.generate_html()
    st.components.v1.html(net_html, height=650)
