import asyncio

import networkx as nx
import matplotlib.pyplot as plt

from gnn.main import SRC_PATH
from utils.utils import GraphUtils


def visualize_graph(G, layout="spring", node_size=300, edge_width=1.0, with_labels=True):
    """
    Visualizes a NetworkX graph using various layouts.

    :param G: NetworkX graph object
    :param layout: Graph layout ("spring", "circular", "kamada_kawai", "shell", "random", or "graphviz")
    :param node_size: Size of nodes
    :param edge_width: Width of edges
    :param with_labels: Whether to show labels
    """
    if G is None or len(G.nodes) == 0:
        print("Graph is empty or None. Cannot visualize.")
        return

    # Choose layout
    if layout == "spring":
        pos = nx.spring_layout(G, seed=42)
    elif layout == "circular":
        pos = nx.circular_layout(G)
    elif layout == "kamada_kawai":
        pos = nx.kamada_kawai_layout(G)
    elif layout == "shell":
        pos = nx.shell_layout(G)
    elif layout == "random":
        pos = nx.random_layout(G)
    elif layout == "graphviz":
        try:
            from networkx.drawing.nx_agraph import graphviz_layout
            pos = graphviz_layout(G, prog="dot")  # Uses Graphviz
        except ImportError:
            print("Graphviz not installed. Falling back to 'spring' layout.")
            pos = nx.spring_layout(G, seed=42)
    else:
        print(f"Unknown layout '{layout}', defaulting to 'spring'.")
        pos = nx.spring_layout(G, seed=42)

    # Ensure correct Matplotlib backend
    plt.switch_backend('TkAgg')  # Fixes GUI-related issues
    plt.figure(figsize=(8, 6))

    ax = plt.gca()  # Ensure proper axis handling

    nx.draw(
        G,
        pos,
        with_labels=with_labels,
        node_size=node_size,
        edge_color="gray",
        width=edge_width,
        font_size=10,
        font_weight="bold",
        ax=ax  # Explicitly pass the correct axis
    )

    plt.title(f"NetworkX Graph ({layout} Layout)")
    plt.show()


if __name__ == "__main__":
    g_utils = asyncio.run(GraphUtils.create(general_stuff=SRC_PATH, test=True))
    visualize_graph(g_utils.G, layout="shell", node_size=100, edge_width=0.5, with_labels=True)

