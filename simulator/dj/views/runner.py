import os

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


from bm.settings import TEST_USER_ID

from utils.graph.get_utils import get_graph_utils
from utils.simulator.world.create_world import CreateWorld
from utils.simulator.world.run_world import WorldRunner


import asyncio


LOAD_GRAPHP=r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\local_graph"

class S(serializers.Serializer):
    user_id = serializers.CharField(
        required=False,
        default=TEST_USER_ID
    )
    env_id = serializers.CharField(
        help_text="ID of ENV that should be run",
        default="env_rajtigesomnlhfyqzbvx"
    )


components= {
    "electron": 5,  # 1e20,   # 100,000,000,000,000,000,000 electrons per m³
    "proton": 5,  # 1e19,  # 10,000,000,000,000,000,000 protons per m³
    "neutron": 5,  # 1e15,   # 1,000,000,000,000,000 neutrons per m³
    "qf": {
        "shape": "rect",
        "dim": [25, 25, 2]
    }
}

class WorldRunnerTestView(APIView):
    serializer_class = S
    testing=True
    def post(self, request):
        """
        Entry is alltimes 2 nodes with a edge connection
        """

        data = request.data
        user_id = data.get("user_id", TEST_USER_ID)
        env_id = data.get("env_id", "env_bare_rajtigesomnlhfyqzbvx")
        if env_id is None or len(env_id.strip()) == 0:
            env_id = "env_bare_rajtigesomnlhfyqzbvx"

        g_path = os.path.join(LOAD_GRAPHP, f"{env_id}.json")

        # validate needed Graph
        g_obj = get_graph_utils(
            local=self.testing,
        )

        # create
        print("Create Graph")
        g = g_obj(
            upload_to="bq",
            database="brainmaster",
            nx_only=True,
            g_from_path=g_path
        )

        if not os.path.exists(g_path):
            world_creator = CreateWorld(g, components, world_type="bare", user_id=TEST_USER_ID)

            asyncio.run(world_creator.hello_world())
            # available_functions = DEF_ARG_EXTRACTOR.match_to_powerset(key_combos)
        else:
            print("Graph already exists")

        world_runner = WorldRunner(
            g,
            env_id,
            user_id,
            local_g_path=g_path
        )

        world_runner.run()

        # return StreamingHttpResponse({"status": "success"}, status=200)
        return Response({"status": "success"}, status=200)








