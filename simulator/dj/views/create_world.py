import asyncio

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from _google.graph.g_utils import GGraphUtils
from bm.settings import TEST_USER_ID
from utils.graph.get_utils import get_graph_utils
from utils.simulator.world.create_world import CreateWorld

components= {
    "electron": 5,  # 1e20,   # 100,000,000,000,000,000,000 electrons per m³
    "proton": 5,  # 1e19,  # 10,000,000,000,000,000,000 protons per m³
    "neutron": 5,  # 1e15,   # 1,000,000,000,000,000 neutrons per m³
    "qf": {
        "shape": "rect",
        "dim": [25, 25, 2]
    }
}

"""
"positron": 1e12,   # 1,000,000,000,000 positrons per m³
"photon":   1e25,   # 10,000,000,000,000,000,000,000,000 photons per m³
"alpha":    1e16,   # 10,000,000,000,000,000 helium nuclei per m³
"muon":     1e10,   # 10,000,000,000 muons per m³
"""


class S(serializers.Serializer):
    world_type = serializers.CharField(
        help_text="World type ",
        required=False,
        default="bare"
    )


class CreateWorldView(APIView):
    serializer_class = S
    testing=True
    def post(self, request):
        """
        Entry is alltimes 2 nodes with a edge connection
        """

        data = request.data
        world_type = data.get("world_type", "bare")  # bare || cellular

        # available_functions = DEF_ARG_EXTRACTOR.match_to_powerset(key_combos)
        # validate needed Graph
        g_obj = get_graph_utils(
            local=self.testing,
        )

        # create
        print("Create Graph")
        g = GGraphUtils(
            upload_to="bq",
            database="brainmaster",
            nx_only=True,
            g_from_path=None
        )

        world_creator = CreateWorld(g, components, world_type, user_id=TEST_USER_ID)

        asyncio.run(world_creator.hello_world())
        return Response({"status": "success"}, status=200)



"""
Problem: variable names are not constant -> sys gets highly error prune 
-> embed semantic meaning of each var. 
-> use uniform units in the entire sys (to provide not a value in cm when m is required)
-->> JUST DESIGN IT CONSTANT

BUT 
how to choose the right var at the right position?
semantic 
"""







