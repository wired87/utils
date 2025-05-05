from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from google.cloud import bigquery

from _google import GC_PROJECT_ID
from _google.bq.auth_handler import BQAuthHandler
from physics.world import CreateWorld

bq_auth_handler = BQAuthHandler()

class S(serializers.Serializer):
    table_id = serializers.CharField(
        default="table_id",
        label="table_id",
        help_text="Table ID"
    )
world_creator= CreateWorld()
class GenerateEmbeddingsView(APIView):
    serializer_class = S

    def post(self, request):
        """Generates embeddings for the 'text' field in a BigQuery table."""
        data = request.data
        serializer = self.serializer_class(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        particles = data.get("particle_matrix")

        try:
            # todo outsource task
            world_creator.create()

            return Response({"message": "Embeddings generated successfully."}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
