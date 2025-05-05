import asyncio

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from bm.settings import TEST_USER_ID
from utils.simulator.world.run_world import WorldRunner
from utils.utils import GraphUtils



class S(serializers.Serializer):
    user_id = serializers.CharField(
        required=False,
        default=TEST_USER_ID
    )
    env_id = serializers.CharField(
        help_text="ID of ENV that should be run",
        default="env_rajtigesomnlhfyqzbvx"
    )

class WorldRunnerView(APIView):
    serializer_class = S

    def post(self, request):
        """
        Entry is alltimes 2 nodes with a edge connection
        """

        data = request.data
        user_id = data.get("user_id", TEST_USER_ID)
        env_id = data.get("env_id", "env_rajtigesomnlhfyqzbvx")

        # available_functions = DEF_ARG_EXTRACTOR.match_to_powerset(key_combos)
        g = GraphUtils(
            upload_to="bq",
            sp_dbid="brainmaster",
            nx_only=True
        )
        world_runner = WorldRunner(
            g,
            env_id,
            user_id,
        )
        world_runner.run()
        # return StreamingHttpResponse({"status": "success"}, status=200)
        return Response({"status": "success"}, status=200)








