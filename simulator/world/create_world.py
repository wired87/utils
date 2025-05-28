
r"""
👉 Ions create electric fields by moving around.
👉 Electric fields guide ions.
👉 This feedback loop is what you simulate.
- the keys to intelligence lies in ion interaction
"""

import os

from _google.firebase.real_time_database import FirebaseRTDBManager
from _google.graph.g_utils import GGraphUtils
from bm.settings import TEST_USER_ID
from physics.quantum_fields.qf_creator import QFCreator
from utils.file.yyaml import load_yaml
from utils.graph.local_graph_utils import LocalGraphUtils
from utils.graph.visual import create_g_visual
from utils.math import MGLOBALSC
from utils.simulator.utils.mover import Mover
from utils.simulator.world.env.env_creator import ENVCCreator



class WorldCore:
    def __init__(self, g, user_id=None):
        self.g = g

        self.user_id = user_id or TEST_USER_ID
        self.graph_name = "BRAINMASTER"
        self.ion_types = [
            "CL",
            "CA2",
            "Na",
            "K",
            "M",
            "P"
        ]


class CreateWorld:
    """
    Creator for bare empty sim World


    Start/Change ->
    Adapt Config ->
    Model Changes ->
    Results Upload Graph ->
    Render.
    """
    """
    Workflow
    Collect reactions
    Create Graph
    Simulate interactions
    """

    def __init__(
            self,
             g:LocalGraphUtils or GGraphUtils,
            components,
            world_type="bare",
            user_id=TEST_USER_ID,
    ):
        self.user_id = user_id
        self.world_type=world_type
        self.components = components

        self.spread_items_type = [
            "QFN"
        ]

        self.g = g
        self.raw = True  # upload without linking anything
        self.filter_for = "EXPERIMENT_accession_"
        self.size = 0
        self.batch_size = 10
        self.graph_name = "BRAINMASTER"
        self.testing = True

        self.env_creator=ENVCCreator(self.g, TEST_USER_ID, world_type=world_type)
        fb_path = f"users/{user_id}/env/{self.env_creator.envc_id}"
        self.image_path = r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\world01.json"
        self.mover=Mover(g)

        print("Set fb path", fb_path)

        self.custom_firebase = FirebaseRTDBManager(base_path=fb_path)
        self.run_batch_gcp = True
        self.testing = True
        self.current_file = None

        self.ion_count = 0

        self.overall_modulator_args = {
            "pos_x": 0.0,
            "pos_y": 0.0,
            "pos_r": 0.0
        }

        self.modulators = {
            "preasure": {},
            "voltage": {},
            "break_ecm_junctions": {},
            "cutting_event": {}
        }

        self.m_globals = MGLOBALSC.copy()




    async def hello_world(self):
        print("create world")
        
        # ENV
        self.dim, env_c = self.env_creator.create()

        #if self.world_type == "bare":
        """particle_creator = ParticleCreator(
            g=self.g,
            env_id=self.env_creator.envc_id,
        )
        particle_creator.create(
            particle_conc=self.particle_conc
        )"""

        self.qf_creator = QFCreator(
            g=self.g,
            env_id=self.env_creator.envc_id,
            testing=self.testing,
            specs=self.components["qf"]
        )

        self.qf_creator.create()

        self.connect_meta_nodes()

        # Bring in initial shape
        # todo spread richtet sich nicht nach dim(w-h-d), dim richtet sich nach anzahl und anordnung qfns
        self.spread_connect_items()

        self.g.print_status_G()

        # Save world image for PyVis
        create_g_visual(self.g.G, dest_path=self.image_path)

        # Firebase action
        #self.g.upsert_firebase(fb_dest=f"users/{self.user_id}/env/{self.env_creator.envc_id}/", testing=self.testing)

        #time.sleep(30)
        print("creation process finished")
        return env_c

    def connect_meta_nodes(self):
        print("Connect nodes")

        edge_yaml_cache = {}

        for nid, args in self.g.G.nodes(data=True):
            for nnid, nargs in self.g.G.nodes(data=True):
                # Just connect Meta/Parent objects here (QF- not QFN)
                src_layer = args.get('type')
                trgt_layer = nargs.get('type')
                if nid != nnid and (src_layer == "ENV" or src_layer == "QF") and (trgt_layer == "ENV" or trgt_layer == "QF"):
                    edge_def = args.get("EC", {}).get(trgt_layer)
                    if not edge_def:
                        continue

                    edge_key = edge_def["edge_attrs"]
                    if edge_key not in edge_yaml_cache:
                        edge_yaml_cache[edge_key] = load_yaml(os.path.abspath(edge_key))
                    if edge_def.get("rel") is None:
                        print("edge_def rel", edge_def)
                        print("edge_def ATTRS", args)
                    if isinstance(edge_yaml_cache[edge_key], list):
                        print("LIST RECOGNIZED:", edge_yaml_cache[edge_key])
                    self.g.add_edge(
                        src=nid,
                        trt=nnid,
                        attrs=dict(
                            src_layer=src_layer,
                            trgt_layer=trgt_layer,
                            rel=edge_def["rel"],
                            **edge_yaml_cache[edge_key],
                        )
                    )

        # remove the path specs from each node
        for nid, args in self.g.G.nodes(data=True):
            if args.get("type") not in ["USERS", "PARAMETER", "EQUATION"]:
                if "EC" in args.keys():
                    args.pop("EC")
                    self.g.G.nodes[nid].update(args)

        print("All Parent Nodes Connected")

    def spread_connect_items(self, connect_nearest=8):
        dx_set = False
        for item in self.spread_items_type:
            spread_items = [
                (nid, attrs) for nid, attrs in self.g.G.nodes(data=True) if
                attrs.get("type") == item
            ]

            print(f"spread {len(spread_items)} items")

            # SPREAD ITEMS OVER VIRTUAL AREA
            for nid, attrs in spread_items:
                # print("Dpread item", nid)
                self_attrs, dx = self.mover.spread_objects_3d(
                    amount_items=len(spread_items),
                    dim=self.dim[0],
                    self_attrs=attrs
                )

                # SET NODE DISTANCE FOR LAPLACIAN
                if dx_set is False:
                    for k,v in self.g.G.nodes(data=True):
                        if v.get("type") == "ENV":
                            v["dx"] = float(dx) * float(self.m_globals["px_to_meter"])
                            self.g.G.nodes[k].update(v)
                            dx_set=True

                self.g.G.nodes[nid].update(self_attrs)
            else:
                print("Item not in init mode -> not spread")

            # Connect nearest QFN neighbors
            # Reinit spread_items since last changes
            spread_items = [
                (nid, attrs) for nid, attrs in self.g.G.nodes(data=True) if
                attrs.get("type") == item
            ]

            for nid, attrs in spread_items:
                nearest_neighbors = self.mover.get_nearest_neighbors(
                    start_pos=attrs.get("pos"),
                    neighbors=spread_items,
                    amount_neighbors=connect_nearest,
                    pos_attr_key="pos"
                )

                # Connect all nodes
                for neighbor in nearest_neighbors:
                    #print("Connect ", nid, "->", neighbor[0])
                    self.g.add_edge(
                        nid,
                        neighbor[0],
                        attrs=dict(
                            src_layer=item,
                            trgt_layer=neighbor[1].get("type"),
                            rel="neighbor"
                        )
                    )

                    # Connect all fields direct
                    self.qf_creator.connect_field_types(
                        src_qfn_id=nid,
                        trgt_qfn_id=neighbor[0]
                    )

                self.g.G.nodes[nid].update(attrs)
