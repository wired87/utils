import pygame


class PyGameRenderer:

    def __init__(self,g_utils, screen, scale):
        self.g_utils=g_utils
        self.scale = scale
        self.screen = screen

    def render(self, self_attrs, nid, scale, trgt_node_type="CELL"):
        # render
        #print("render", nid)
        self.render_circle(self_attrs)
        self.render_edges(nid, self_attrs, trgt_node_type)

    def render_circle(self, attrs):
        pos = self.get_pos(attrs)
        r = float(attrs.get("radius", 5))
        mf = float(attrs.get("multiplication_factor", 1))
        color = (255, 255, 255) #attrs.get("color")

        """
        print("r", r)
        print("mf", mf)
        print("color", color)
        """

        pygame.draw.circle(
            self.screen,
            color,
            pos,
            r * mf
        )

    def get_pos(self, attrs):
        pos = (int(attrs.get("pos")[0]), int(attrs.get("pos")[1]))
        #print("PG pos:", pos)
        return pos

    def render_edges(self, nid, attrs, trgt_node_type=None):
        for neighbor in self.g_utils.G.neighbors(nid):
            n_attrs = self.g_utils.G.nodes[neighbor]
            if trgt_node_type is not None:
                if n_attrs.get("type", None) == trgt_node_type:
                    self.draw_edge_between(src_attrs=attrs, trgt_attrs=n_attrs)
            else:
                self.draw_edge_between(src_attrs=attrs, trgt_attrs=n_attrs)




    def draw_edge_between(self, src_attrs, trgt_attrs, color=(200, 200, 200), width=1):
        src_pos = self.get_pos(src_attrs)
        trgt_pos = self.get_pos(trgt_attrs)
        pygame.draw.line(self.screen, color, src_pos, trgt_pos, width)
