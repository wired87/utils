import asyncio

from bm.settings import TEST_USER_ID
from physics.particles.particle_creator import ParticleCreator
from utils.simulator.world.env.env_creator import ENVCCreator
from utils.utils import GraphUtils


class WorldCore:
    def __init__(self, user_id=None):
        self.g = GraphUtils(upload_to="sp", cache_only=False)

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

    def __init__(self, g:GraphUtils, particle_conc, world_type="bare", user_id=None):
        self.user_id = user_id
        self.world_type=world_type
        self.particle_conc = particle_conc
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
        particle_creator = ParticleCreator(
            g=self.g,
            env_id=self.env_creator.envc_id,
        )
        particle_creator.create(
            particle_conc=self.particle_conc
        )

        self.g.print_status_G()

        print("Start batch")
        if self.g.upload_to == "sp":
            await self.g.acreate_session()
        await self.g.abatch_commit()

        """# Create Spanner Graph
        print("Create Spanner Graph")
        node_tables, edge_tables = self.g.filter_table_names(self.g.schemas.keys())
        self.g.create_graph(
            node_tables=node_tables,
            edge_tables=edge_tables,
            graph_name=self.graph_name,
        )"""

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



r"""
👉 Ions create electric fields by moving around.
👉 Electric fields guide ions.
👉 This feedback loop is what you simulate.
- the keys to intelligence lies in ion interaction
"""
