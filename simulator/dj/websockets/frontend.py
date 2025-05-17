from channels import db
from channels.generic.websocket import AsyncWebsocketConsumer

from urllib.parse import parse_qs
from firebase_admin import db

import json
import asyncio
import random
import logging

from _google.firebase.real_time_database import FirebaseRTDBManager
from utils.graph.get_utils import get_graph_utils

logger = logging.getLogger(__name__)

class SimulationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Query-Params extrahieren
        query_string = self.scope["query_string"].decode()
        query_params = parse_qs(query_string)

        self.user_id = query_params.get("user_id", [None])[0]
        self.env_id = query_params.get("env_id", [None])[0]

        if not self.user_id or not self.env_id:
            await self.close()
            return

        self.db_base_path = f"users/{self.user_id}/env/{self.env_id}/"

        try:
            # Todo improve auth (token, email,...)
            db_ref = db.reference(self.db_base_path)
            if not db_ref:
                await self.close()
                return
        except Exception as e:
            print("Request denied:", e)
            await self.close()
            return


        await self.accept()

        self.firebase = FirebaseRTDBManager(self.user_id)

        # validate needed Graph
        g_obj = get_graph_utils(
            local=True,
        )

        # create
        print("Create Graph")
        self.g = g_obj(
            upload_to="fb",
            database="brainmaster",
            nx_only=True,
            g_from_path=None
        )

        self.g, env_id, env_attrs = self.g._request_env_tree(
            self.g,
            path=self.db_base_path
        )

        self.listener_thread = db_ref.listen(
            self.handle_data_change
        )

        await self.send(
            text_data=json.dumps({
                "type": "handshake",
                "status": "connection established"
                }
            )
        )

        self.stream_task = asyncio.create_task(self.stream_firebase_data())



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

    def walk_g_tree(self, path, node_attrs):
        walk_attrs = node_attrs
        for item in path:
            walk_attrs = walk_attrs[item]
        return walk_attrs



    def handle_data_change(self, event):
        """
        Diese Funktion wird aufgerufen, wenn sich Daten am beobachteten Pfad ändern.
        """
        print("Datenänderung erkannt!")
        print(f"Event-Typ: {event.event_type}")  # 'put' oder 'patch'
        print(f"Pfad: {event.path}")  # Der geänderte Unterpfad (relativ zur Referenz)
        print(f"Neue Daten: {event.data}")  # Die neuen Daten am geänderten Pfad

        # Hier können Sie Ihre Backend-Logik basierend auf der Änderung implementieren
        self.db_base_path = f"users/{self.user_id}/env/{self.env_id}/"

        # Check for field changes of interest
        if "pos" in event.path or "color" in event.path:
            parts = event.path.split("/")
            node_type = parts[0]
            node_id = parts[1]
            path_from_node = parts[1:]

            # Update the local Graph from
            if node_type == "edge":
                parts = node_id.split("_")

                edge_attrs=self.g.G[parts[0]][parts[2]]
                if edge_attrs:
                    edge_attrs=self.walk_g_tree(path_from_node, node_attrs=edge_attrs)
                    if edge_attrs != event.data:

                    self.g.G[parts[0]][parts[2]].update(edge_attrs)
            else:
                node_attrs=self.g.G.nodes[node_id]
                if node_attrs:
                    node_attrs = self.walk_g_tree(path_from_node, node_attrs=node_attrs)
                    self.g.G.nodes[node_id].update(node_attrs)

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

    async def stream_firebase_data(self):
        logger.info("Starting Firebase polling loop.")
        try:
            while True:
                if updated_data:
                    await self.send_data_update({
                        "type": "data_update",
                        "data": updated_data
                    })
        except asyncio.CancelledError:
            logger.info("Firebase polling cancelled.")
        except Exception as e:
            logger.error(f"Error in Firebase stream: {e}")
            await self.send_data_update({
                "type": "error",
                "message": str(e)
            })


