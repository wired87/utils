import asyncio

import pygame

from bm.logging_custom import cpr
from bm.settings import TEST_USER_ID
from physics import STANDARD_MODELC, POSC, GRAVITYC, CORE_LAWS_C
from physics.particles.particle_updator import ChargedParticleHandler
from physics.putils.calculator import Calculator
from utils.simulator.world.env.env_updator import QFHandler
from utils.pygame.renderer import PyGameRenderer
from utils.simulator.utils.mover import Mover


class WorldRunner:
    """
    Loads the env with all objects and sims them
    Each loop represents a timestep (on that way,
    real time is not a problem anymore)

    ToDO: At the end we just need to create a powerset
    of all possible equation combis / cases, for all
    nodes to update them.


    Start jut with movement (so you can show something)->
    fake till make
    """

    def __init__(self, g, env_id: str, user_id=TEST_USER_ID, local_g_path=None):

        self.g = g

        self.env_id = env_id
        self.scale = 1e7
        self.ion_scale = 1e9
        self.fps = 60
        self.clock = pygame.time.Clock()

        self.amount_cells = None
        self.width = None
        self.height = None
        self.pg_renderer = None
        self.screen = None
        self.screen = None

        """self.wol = WorldObjectLoader(
            g,
            env_id,
            user_id,
            local_g_path=local_g_path
        )"""

        self.charged_particle_handler = ChargedParticleHandler(
            g, user_id
        )

        self.qf_handler = QFHandler(
            g,
            user_id
        )

        self.cell_positions = {}
        self.g = g
        self.user_id = user_id

        self.T = None
        self.D = None

        self.testing = True
        self.mover = Mover(self.g)
        # CLASSES
        # self.env_up = ENVUpdator()
        self.calculator = Calculator(
            g,
            calculations=list(
                # QF Equations
                STANDARD_MODELC +

                # Particle Equations
                CORE_LAWS_C +
                POSC +
                GRAVITYC
            )
        )
        # Particles include in the initial spread process
        self.spread_items_type = [
            "PARTICLE"
        ]

    def init_world(self):
        pygame.init()
        # asyncio.run(self.wol.load_local_graph())
        # init env
        for nid, attrs in self.g.G.nodes(data=True):
            if attrs.get("type") == "ENV":
                print("ENV attrs", attrs)
                screen_dim = attrs.get("dim")
                self.height = screen_dim[1]
                self.width = screen_dim[0]
                # self.amount_cells = attrs.get("cell_concentration")

        # Init Surface
        print("screen_dim", self.width, self.height)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Particle Field Simulation")

        # Init PG Renderer
        self.pg_renderer = PyGameRenderer(
            self.g,
            screen=self.screen,
            scale=self.scale
        )

        # Spread items
        print("World initialized")

    def spread_items(self):
        spread_items = [
            (nid, attrs) for nid, attrs in self.g.G.nodes(data=True) if
            attrs.get("type") in self.spread_items_type
        ]
        for nid, attrs in spread_items:
            init = attrs.get("init")
            if init is True:
                self_attrs = self.mover.spread_objects(
                    amount_items=len(spread_items),
                    screen_width=self.width,
                    screen_height=self.height,
                    self_attrs=attrs
                )
                self.g.G.nodes[nid].update(self_attrs)


    #def get_

    def update_loop(self):
        # todo added nodes while loop jsut added after finish -> check after each iter for changes -> continue loop with switched G
        stuff = [(nid, attrs) for nid, attrs in self.g.G.nodes(data=True)]
        len_stuff = len(stuff)
        env_attrs = self.g.G.nodes[self.env_id]
        index = 0

        while index < len_stuff:
            # validate item
            updated_len_stuff = len(stuff)
            if len_stuff < updated_len_stuff:
                index -= (updated_len_stuff - len_stuff)

            nid, attrs = stuff[index]
            node_type=attrs.get("type")

            # Loop through each other item
            nindex = 0
            while nindex < len_stuff:
                # validate item
                updated_len_stuff = len(stuff)
                if len_stuff < updated_len_stuff:
                    nindex -= (updated_len_stuff - len_stuff)

                nnid, nattrs = stuff[nindex]
                if nid != nnid:

                    # Get Stuff
                    edge_attrs = self.g.G.edges[nid, nnid]

                    self.calculator.main(
                        parent=attrs,
                        child=nattrs,
                        edge_attrs=edge_attrs,
                        env_attrs=env_attrs
                    )

                # todo: impl. check for node type -> see Wasteleands (bottom)
                # todo implement neuron logic -> connect nearest 10 ->

                nindex += 1
            index += 1
            self.render(node_type, attrs, nid)

    def render(self, node_type, attrs, nid):

        if node_type == "PARTICLE":
            # todo calc i each run the exact shape of the cell to adapt the sa on it
            self.pg_renderer.render(attrs, nid, scale=self.scale)

    def render_edges(self):
        for src, trgt in self.g.G.edges():
            # print("src, trgt", src, trgt)
            src_attrs = self.g.G.nodes[src]
            trgt_attrs = self.g.G.nodes[trgt]

            # Skip invalid edge IDs
            src_type = src_attrs.get("type")
            trgt_type = trgt_attrs.get("type")
            # print("src_type LINE:", src_type, trgt_type)

            if src_type == "PARTICLE" and trgt_type == "PARTICLE":
                src_pos = src_attrs.get("pos")
                trgt_pos = trgt_attrs.get("pos")

                start = (src_pos[0], src_pos[1])
                end = (trgt_pos[0], trgt_pos[1])
                # print("DRAW LINE:", f"{src}:{src_type}:{start}", f"{trgt}:{trgt_type}:{end}")

                pygame.draw.line(self.screen, (0, 0, 255), start, end, width=1)

        # asyncio.run(self.g.batch_commit())

    def update_G(self):
        # Update G
        for k, v in self.g.schemas.items():
            # Update nodes
            for item in v["rows"]:
                self.g.G.add_node(
                    item["id"],
                    **{k: v for k, v in item.items() if k != "id"}
                )
                v["rows"] = []
        # Update edges
        for item in self.g.cache:
            self.g.G.add_edge(
                item["src"],
                item["trgt"],
                attrs={k: v for k, v in item.items() if k not in ["src", "trt"]},
            )
        self.g.cache = []

        # Rm nodes & reset
        self.g.clear_cache()
        self.g.cache_trash = []

    def run(self):
        """For changes of cell / env (intra<->extra) graph repr way better"""

        # -< einfach ions in cell darstellen ->
        # asyncio.run(self.wol.load_objects())
        self.init_world()
        running = True
        index = 0
        while running:
            index += 1
            # todo get direct cell & ion neighbor from pos -> in feedback loop
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos

            if pygame.key.get_pressed()[pygame.K_ESCAPE]:
                break

            self.screen.fill((0, 0, 0))  # Black

            # Update Objects
            self.update_loop()

            # Render objects

            pygame.display.update()

        pygame.quit()



"""
node_type = attrs.get("type")

            if node_type == "PARTICLE":
                asyncio.run(self.charged_particle_handler.update(nid, attrs))
            elif node_type == "QF_NODE":
                self.qf_handler.update(
                    nid,
                    attrs
                )

"""