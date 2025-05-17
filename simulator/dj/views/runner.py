import asyncio
import os

from django.http import StreamingHttpResponse
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from _google.firebase.real_time_database import FirebaseRTDBManager
from bm.settings import TEST_USER_ID
from physics.quantum_fields.qf_updator import QFUpdator
from utils.graph.get_utils import get_graph_utils
from utils.simulator.world.create_world import CreateWorld
from utils.simulator.world.run_world import WorldRunner

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

class WorldRunnerView2(APIView):
    serializer_class = S
    testing=True
    def post(self, request):
        """

        Starts a simulation and pushes the result to firebase
        todo make a webhook from it to receive stimuli commands
        """

        data = request.data
        user_id = data.get("user_id", TEST_USER_ID)

        env_id = data.get("env_id", "env_bare_rajtigesomnlhfyqzbvx")
        if env_id is None or len(env_id.strip()) == 0:
            env_id = "env_bare_rajtigesomnlhfyqzbvx"

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
            g_from_path=None
        )

        base_path=f"env/{env_id}"
        path = f"users/{user_id}/{base_path}/"

        fb_manager=FirebaseRTDBManager(user_id)

        data = fb_manager.get_data(path=path)



        qf_updator = QFUpdator(
            g=g,
            user_id=user_id
        )

        qf_updator.update(
            env_attrs
        )

        # Upsert G to FireBase
        g.upsert_firebase(
            user_id=user_id,
            env_id=env_id
        )






class SimFrontendView(APIView):
    serializer_class = S
    def get_script(
            self,
            api_key: str,
            project_id: str,
            firebase_rtdb: str,
            sender_id: str,
            app_id: str,
            listen_path: str = "nodes",  # Parameter für den Pfad, der per Listener beobachtet wird
            bubble_data_endpoint: str = "/api/bubble-data/",  # Parameter für den DRF Endpunkt
            chart_title: str = "Live Simulation Bubble Chart",  # Parameter für den Diagrammtitel
            chart_width: str = "900px",  # Parameter für die Diagrammbreite (CSS-Format)
            chart_height: str = "500px",  # Parameter für die Diagrammhöhe (CSS-Format)
            html_title: str = "Simulation Live Data",  # Parameter für den HTML <title>
            main_heading: str = "Simulation Live-Daten"  # Parameter für den Haupt-H1-Titel
    ) -> str:

        return f"""
               <!DOCTYPE html>
            <html>
            <head>
              <title>Hi</title>
              <script src="https://www.gstatic.com/firebasejs/9.22.2/firebase-app-compat.js"></script>
              <script src="https://www.gstatic.com/firebasejs/9.22.2/firebase-database-compat.js"></script>
              <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
            </head>
            <body>
              <script>
                
            
                // 📊 BUBBLE CHART
                google.charts.load('current', {{ packages: ['corechart'] }});
                google.charts.setOnLoadCallback(drawChart);
            
                async function drawChart() {{
                  const response = await fetch('/api/bubble-data/');  // DRF Endpoint
                  const jsonData = await response.json();
                  //const dataArray = [['ID', 'X', 'Y', 'Label', 'Size']];
            
                  for (const point of jsonData.data) {{
                    dataArray.push([point.id, point.x, point.y, point.label, point.size]);
                  }}
            
                  const data = google.visualization.arrayToDataTable(dataArray);
            
                  const options = {{
                    title: 'Live Bubble Chart from DRF Backend',
                    hAxis: {{ title: 'X-Axis' }},
                    vAxis: {{ title: 'Y-Axis' }},
                    bubble: {{ textStyle: {{ fontSize: 11 }} }},
                    animation: {{ duration: 500, easing: 'out', startup: true }}
                  }};
            
                  const chart = new google.visualization.BubbleChart(document.getElementById('chart_div'));
                  chart.draw(data, options);
                }}
              </script>
            
              <h1></h1>
              <div id="log"></div>
            
              <h2>Best Brain</h2>
              <div id="chart_div" style="width: 900px; height: 500px;"></div>
            </body>
            </html>
            """
    def get(self, request):
        """
        Retrieves stimuli data from firebase wraps it in html and sends it to the frontend
        todo: webhook, spanner
        """

        data = request.data
        user_id = data.get("user_id", TEST_USER_ID)

        env_id = data.get("env_id", "env_bare_rajtigesomnlhfyqzbvx")
        if env_id is None or len(env_id.strip()) == 0:
            env_id = "env_bare_rajtigesomnlhfyqzbvx"

        # validate needed Graph
        g_obj = get_graph_utils(
            local=False,
        )

        # create
        print("Create Graph")
        g = g_obj(
            upload_to="bq",
            database="brainmaster",
            nx_only=True,
            g_from_path=None
        )

        base_path = f"env/{env_id}"
        path = f"users/{user_id}/{base_path}/"

        fb_manager = FirebaseRTDBManager(user_id)

        data = fb_manager.get_data(path=path)

        print("Data received")
        # load the graph with data
        env_attrs = None
        for node_type, node_id in data.items():
            for nid, attrs in node_id.items():
                if node_type == "edges":
                    parts = nid.split("_")
                    g.add_edge(
                        parts[0],
                        parts[1],
                        attrs=attrs
                    )
                elif node_type == "ENV":
                    env_attrs = attrs
                    env_id = nid
                else:
                    g.add_node(
                        dict(
                            id=nid,
                            **attrs
                        )
                    )

        return StreamingHttpResponse({"status": "success"}, status=200)


# consumers.py (in your Django app)

import json
import asyncio
import networkx as nx # Assuming you have networkx installed
import random # For simulating data changes
import logging

logger = logging.getLogger(__name__)


def create_initial_graph():
    G = nx.Graph()
    # Add some nodes with initial positions and types
    G.add_node("node1", type="typeA", x=50, y=50, label="Node 1", size=10, color="red")
    G.add_node("node2", type="typeB", x=150, y=100, label="Node 2", size=15, color="blue")
    G.add_node("node3", type="typeA", x=100, y=200, label="Node 3", size=12, color="green")
    G.add_node("node4", type="typeC", x=250, y=150, label="Node 4", size=8, color="purple")
    G.add_edge("node1", "node2")
    G.add_edge("node1", "node3")
    G.add_edge("node2", "node4")
    return G

# Global (or shared) graph instance for simplicity in this example
# In production, consider a more robust shared state mechanism
SIM_GRAPH = create_initial_graph()
# --- End Simulation Placeholder ---


class SimulationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer to send real-time simulation data updates.
    Simulates looping through a graph and sending updates.
    """

    async def connect(self):
        """Called when the websocket is handshaking as part of initial connection."""
        logger.info("WebSocket connected.")
        await self.accept()

        # Start the simulation loop in a background task
        # We pass the graph and the consumer instance to the loop
        self.simulation_task = asyncio.create_task(
            self.run_simulation_loop(SIM_GRAPH)
        )

    async def disconnect(self, close_code):
        """Called when the websocket is disconnected."""
        logger.info(f"WebSocket disconnected with code: {close_code}")
        # Cancel the simulation task when the client disconnects
        if hasattr(self, 'simulation_task'):
            self.simulation_task.cancel()
            try:
                await self.simulation_task # Wait for cancellation to complete
            except asyncio.CancelledError:
                logger.info("Simulation loop task cancelled.")
        pass

    async def receive(self, text_data):
        """
        Called when a message is received from the websocket.
        (Optional: Implement logic to receive commands from the frontend)
        """
        logger.info(f"Received message from frontend: {text_data}")
        # Example: Parse JSON message from frontend
        # text_data_json = json.loads(text_data)
        # command = text_data_json.get('command')
        # if command == 'start_sim':
        #    self.simulation_task = asyncio.create_task(self.run_simulation_loop(SIM_GRAPH))
        # elif command == 'stop_sim':
        #    if hasattr(self, 'simulation_task') and not self.simulation_task.done():
        #        self.simulation_task.cancel()


    async def send_data_update(self, event):
        """
        Helper method to send a data update message to the frontend.
        Called by the simulation loop.
        """
        # 'event' is the dictionary passed from the loop
        await self.send(text_data=json.dumps(event))
        # logger.debug(f"Sent update: {event}") # Use debug level for frequent sends

    async def run_simulation_loop(self, graph):
        """
        Simulates a loop that processes the graph and sends updates.
        This runs in a separate task within the consumer's event loop.
        """
        logger.info("Simulation loop started.")
        try:
            while True:
                # --- Simulate Graph Processing and Data Update ---
                # Iterate through nodes and simulate changing some data
                for node_id, attrs in list(graph.nodes(data=True)): # Iterate over a copy if modifying graph structure
                    # Simulate a small change in position and size
                    attrs['x'] += random.uniform(-5, 5)
                    attrs['y'] += random.uniform(-5, 5)
                    attrs['size'] = max(5, attrs['size'] + random.uniform(-1, 1)) # Ensure size is not too small

                    # Prepare the update message for this specific node
                    # The frontend needs the ID to know which bubble to update
                    update_message = {
                        'type': 'node_update', # Indicate the type of update
                        'id': node_id,
                        'data': {
                            'x': attrs['x'],
                            'y': attrs['y'],
                            'size': attrs['size'],
                            # Include other relevant data if needed for the frontend
                            'label': attrs.get('label', node_id),
                            'color': attrs.get('color', 'gray') # Example: send color too
                        }
                    }

                    # Send the update message over the WebSocket
                    await self.send_data_update(update_message)

                    # Add a small delay between sending updates for nodes
                    # Adjust this based on how fast you want updates and client capacity
                    await asyncio.sleep(0.05) # Send update for one node every 50ms

                # Add a longer delay after processing all nodes before the next full iteration
                await asyncio.sleep(1) # Wait 1 second before the next loop through all nodes

        except asyncio.CancelledError:
            logger.info("Simulation loop received cancellation signal.")
            # Clean up if necessary
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")
            # Optionally send an error message to the client
            await self.send(text_data=json.dumps({'type': 'error', 'message': f'Backend simulation error: {e}'}))

        logger.info("Simulation loop finished.")



class WorldRunnerView(APIView):
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








