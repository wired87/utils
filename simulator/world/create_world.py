
r"""
👉 Ions create electric fields by moving around.
👉 Electric fields guide ions.
👉 This feedback loop is what you simulate.
- the keys to intelligence lies in ion interaction
"""



import asyncio
import os

from bm.settings import TEST_USER_ID
from physics.quantum_fields.qf_creator import QFCreator
from utils.file.yaml import load_yaml
from utils.graph.local_graph_utils import LocalGraphUtils
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
             g:LocalGraphUtils, # or GraphUtils for prod
            components,
            world_type="bare",
            user_id=TEST_USER_ID,
    ):
        self.user_id = user_id
        self.world_type=world_type
        self.components = components

        self.g = g
        self.raw = True  # upload without linking anything
        self.filter_for = "EXPERIMENT_accession_"
        self.size = 0
        self.batch_size = 10
        self.graph_name = "BRAINMASTER"
        self.testing = True

        self.run_batch_gcp = True
        self.testing = True
        self.current_file = None
        self.ion_count = 0
        self.env_creator=ENVCCreator(self.g, user_id, world_type=world_type)
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

    async def hello_world(self):
        print("create world")
        
        # ENV
        self.env_creator.create()

        #if self.world_type == "bare":
        """particle_creator = ParticleCreator(
            g=self.g,
            env_id=self.env_creator.envc_id,
        )
        particle_creator.create(
            particle_conc=self.particle_conc
        )"""

        qf_creator = QFCreator(
            g=self.g,
            env_id=self.env_creator.envc_id,
            testing=self.testing,
            specs=self.components["qf"]
        )

        qf_creator.create()

        self.g.print_status_G()

        self.connect_all_nodes()

        self.g.print_status_G()

        if self.testing:
            self.g.save_graph(dest_name=self.g.g_from_path)


    def connect_all_nodes(self):
        print("Connect nodes")

        edge_yaml_cache = {}

        for nid, args in self.g.G.nodes(data=True):
            for nnid, nargs in self.g.G.nodes(data=True):
                if nid != nnid and args.get("type") not in ["USERS", "PARAMETER", "EQUATION"]:
                    src_layer = args.get('type')
                    trgt_layer = nargs.get('type')
                    """print("src", args)
                    print("nargs", nargs)"""

                    edge_def = args.get("EC", {}).get(trgt_layer)
                    if not edge_def:
                        continue

                    edge_key = edge_def["edge_attrs"]
                    if edge_key not in edge_yaml_cache:
                        edge_yaml_cache[edge_key] = load_yaml(os.path.abspath(edge_key))

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
        print("All Nodes Connected")






















    async def reinit(self, tables=True, G=True):
        await self.g.acreate_session()
        if G is True:
            print("del g")
            await self.g.update_db(self.g.drop_graph_query(self.graph_name))
        if tables is True:
            print("Del tables")
            await asyncio.gather(*[
                self.g.update_db(
                    self.g.drop_table_query(k.upper())
                ) for k, v in self.ecm_creator.content["ion_concentration_mM"].items()
            ])
            await asyncio.gather(*[self.g.update_db(self.g.drop_table_query(item.upper())) for item in
                                   ["MEMBRANE", "ENV", "CELL"]])
        print("Tables cleared")




        """# Create Spanner Graph
        print("Create Spanner Graph")
        node_tables, edge_tables = self.g.filter_table_names(self.g.schemas.keys())
        self.g.create_graph(
            node_tables=node_tables,
            edge_tables=edge_tables,
            graph_name=self.graph_name,
        )"""