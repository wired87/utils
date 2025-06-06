from pyvis.network import Network


def create_g_visual(G, dest_path):
    for _, properties in G.nodes.items():
        properties['size'] = 20
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
    net = Network(notebook=False,
                  cdn_resources='in_line',
                  height='1000px',
                  width='100%',
                  bgcolor="#222222",
                  font_color="white"
                  )

    net.barnes_hut()
    net.toggle_physics(False)
    net.set_options(options)

    net.from_nx(G)



    # Force HTML generation
    net.html = net.generate_html()
    with open(dest_path, 'w', encoding="utf-8") as f:
        net.html.encode("ascii", "ignore").decode()  # Removes unsupported characters
        net.html.encode("ascii", "replace").decode()
        f.write(net.html)
    print("html created and saved under:", dest_path)
