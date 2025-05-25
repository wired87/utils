import os

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


from bm.settings import TEST_USER_ID

from utils.simulator.test import SimTester


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
        "dim": [5, 5, 2]
    }
}

class CreateWorldView(APIView):
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
        db_base = f"users/{TEST_USER_ID}/env/env_bare_rajtigesomnlhfyqzbvx/"
        test=SimTester()
        test.run(g_path, user_id, env_id, components, database=db_base)

        # return StreamingHttpResponse({"status": "success"}, status=200)
        return Response({"status": "success"}, status=200)








