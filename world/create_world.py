import asyncio

from bm.settings import TEST_USER_ID
from utils.utils import GraphUtils


class WorldCore:
    def __init__(self, user_id=None):
        self.g_utils = GraphUtils(upload_to="sp", cache_only=False)

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


class CreateGWorld:
    """
    Start/Change ->
    Adapt Config ->
    Model Changes ->
    Results Upload Graph ->
    Render.
    """
    """
    Workflow:

    Collect reactions
    Create Graph
    Simulate interactions
    """

    def __init__(self, g_utils:GraphUtils, user_id=None, gene_functionalities: list or None = None):
        self.user_id = user_id
        self.g_utils = g_utils
        self.raw = True  # upload without linking anything
        self.filter_for = "EXPERIMENT_accession_"
        self.size = 0
        self.batch_size = 10
        self.graph_name = "BRAINMASTER"
        self.testing = True

        self.run_batch_gcp = True
        self.testing = True
        self.current_file = None
        self.spanner_db_id = "brainmaster02"
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

    async def hello_world(self):
        print("create world")















        if self.testing:
            print("process finished")
            self.g_utils.print_status_G()
            return True
        else:
            print("Start batch")
            await self.g_utils.acreate_session()
            await self.g_utils.abatch_commit()

            # Create Spanner Graph
            print("Create Spanner Graph")
            node_tables, edge_tables = self.g_utils.filter_table_names(self.g_utils.schemas.keys())
            self.g_utils.create_graph(
                node_tables=node_tables,
                edge_tables=edge_tables,
                graph_name=self.graph_name,
            )

    async def reinit(self, tables=True, G=True):
        await self.g_utils.acreate_session()
        if G is True:
            print("del g")
            await self.g_utils.update_db(self.g_utils.drop_graph_query(self.graph_name))
        if tables is True:
            print("Del tables")
            await asyncio.gather(*[
                self.g_utils.update_db(
                    self.g_utils.drop_table_query(k.upper())
                ) for k, v in self.ecm_creator.content["ion_concentration_mM"].items()
            ])
            await asyncio.gather(*[self.g_utils.update_db(self.g_utils.drop_table_query(item.upper())) for item in
                                   ["MEMBRANE", "ENV", "CELL"]])
        print("Tables cleared")



r"""
👉 Ions create electric fields by moving around.
👉 Electric fields guide ions.
👉 This feedback loop is what you simulate.
- the keys to intelligence lies in ion interaction
"""
