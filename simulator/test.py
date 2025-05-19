import asyncio
import os

from bm.settings import TEST_USER_ID
from utils.graph.get_utils import get_graph_utils
from utils.simulator.world.create_world import CreateWorld
from utils.simulator.world.run_world import WorldRunner


class SimTester:



    def run(self, g_path, user_id, env_id, components):
        # validate needed Graph
        g_obj = get_graph_utils(
            local=True,
            user_id=user_id,
            env_id=env_id,
        )

        # create
        print("Create Graph")
        g = g_obj(
            upload_to="bq",
            database="brainmaster",
            nx_only=True,
            g_from_path=g_path,
            user_id=user_id,
            env_id=env_id,
        )

        if not os.path.exists(g_path):
            world_creator = CreateWorld(g, components, world_type="bare", user_id=TEST_USER_ID)

            asyncio.run(world_creator.hello_world())
            # available_functions = DEF_ARG_EXTRACTOR.match_to_powerset(key_combos)
        else:
            print("Graph already exists")

        """world_runner = WorldRunner(
            g,
            env_id,
            user_id,
            local_g_path=g_path
        )

        world_runner.run()"""