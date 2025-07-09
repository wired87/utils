import networkx as nx
from pyvis.network import Network


def create_g_visual(G, dest_path):
    print("G", G)
    # filter graph fr frontend
    new_G = nx.Graph()
    for nid, properties in G.nodes(data=True):
        new_G.add_node(
            nid,
            **dict(
                size=20
            )
        )

    for src, trgt, properties in G.edges(data=True):
        new_G.add_edge(
            src,
            trgt,
            **dict(
                size=20
            )
        )

    G = None

    options = '''
        const options = {
          "nodes": {
            "borderWidthSelected": 21,
            "font": {
              "size": 20,
              "face": "verdana"
            }
          }
        }
        '''

    net = Network(
        notebook=False,
        cdn_resources='in_line',
        height='1000px',
        width='100%',
        bgcolor="#222222",
        font_color="white"
    )

    net.barnes_hut()
    net.toggle_physics(True)
    net.set_options(options)

    net.from_nx(new_G)

    # Force HTML generation
    net.html = net.generate_html()
    if dest_path is not None:
        with open(dest_path, 'w', encoding="utf-8") as f:
            f.write(net.html)
        print("html created and saved under:", dest_path)
    else:
        return net.html
