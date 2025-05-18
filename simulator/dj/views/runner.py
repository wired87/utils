import asyncio
import os
import queue
import threading

from channels.generic.websocket import AsyncWebsocketConsumer
from django.http import StreamingHttpResponse
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from _google.firebase.real_time_database import FirebaseRTDBManager
from _google.graph.g_utils import GGraphUtils
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

class InitSimView(APIView):
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

        # Upsert G to FireBase
        g.upsert_firebase(
            user_id=user_id,
            env_id=env_id
        )






class SimFrontendView(APIView):
    serializer_class = S

    def get(self, request):
        """
        Retrieves sim data from firebase wraps it in html and sends it to the frontend
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


from urllib.parse import parse_qs

import json
import asyncio
import random # For simulating data changes
import logging

logger = logging.getLogger(__name__)



class SimulationWebsocket(AsyncWebsocketConsumer):
    """
    Start- and update Entry for each sim.
    """
    STOP_SIGNAL=None





    def _build_inittial_G(self):
        # --- Graph aufbauen ---
        print(f"Thread {threading.current_thread().name}: Baue Graph auf.")
        env_attrs = None
        if self.initial_data is not None:  # Stellen Sie sicher, dass Daten vorhanden sind
            for node_type, node_id_data in self.initial_data.items():
                if isinstance(node_id_data, dict):  # Sicherstellen, dass es ein Dictionary ist
                    for nid, attrs in node_id_data.items():
                        if node_type == "edges":
                            parts = nid.split("_")
                            if len(parts) == 2:  # Grundlegende Validierung
                                self.g.add_edge(
                                    parts[0],
                                    parts[1],
                                    attrs=attrs
                                )
                            else:
                                print(
                                    f"Thread {threading.current_thread().name}: Warnung: Ungültiges Kantenformat: {nid}")
                        elif node_type == "ENV":
                            env_attrs = attrs
                            env_id = nid  # Speichern Sie die env_id, falls benötigt
                        else:
                            self.g.add_node(
                                dict(
                                    id=nid,
                                    **attrs
                                )
                            )
        print(f"Thread {threading.current_thread().name}: Graph aufgebaut.")
        return env_attrs, env_id

    def _run_simulation_logic(self):

        print(f"Thread {threading.current_thread().name}: Simulationslogik gestartet für User {self.user_id}, Env {self.env_id}")

        try:
            print(f"Thread {threading.current_thread().name}: Daten von Firebase erhalten.")
            env_attrs, env_id=self._build_inittial_G()

            # --- QF Updator nutzen und nach Firebase pushen ---
            print(f"Thread {threading.current_thread().name}: Starte QF Updator.")

            # run
            asyncio.run(self.qf_updator.update(env_attrs))

            print(
                f"Thread {threading.current_thread().name}: Simulationslogik abgeschlossen für User {self.user_id}, Env {self.env_id}")

        except Exception as e:
            print(f"Thread {threading.current_thread().name}: FEHLER in Simulationslogik: {e}")
            # Hier können Sie Fehler loggen oder behandeln

    def worker_thread_task(self, q: queue.Queue):
        """
        Dies ist die Funktion, die in einem separaten Thread ausgeführt wird.
        Sie liest Aufgaben aus der Queue und arbeitet sie ab.
        """
        print(f"Worker Thread gestartet: {threading.current_thread().name}")

        while True:
            try:
                # Holt die nächste Aufgabe aus der Queue.
                # block=True: Der Thread wartet hier, bis eine Aufgabe verfügbar ist.
                # timeout=1: Wartet maximal 1 Sekunde, dann wird TimeoutError ausgelöst.
                # Nützlich, um regelmäßig auf das Stopp-Signal zu prüfen.
                task = q.get(block=True, timeout=1)

                # Prüfen, ob das Stopp-Signal empfangen wurde
                if task is self.STOP_SIGNAL:
                    print(f"Worker Thread {threading.current_thread().name}: Stopp-Signal erhalten, beende.")
                    break  # Schleife beenden

                print(f"Worker Thread {threading.current_thread().name}: Verarbeite Aufgabe: {task}")

                task_type = task.get('type')

                if task_type == 'firebase_push':
                    db_path = task.get('path')
                    data_to_push = task.get('data')
                    user_id = task.get('user_id')  # Nehmen wir an, der User ID wird auch übergeben

                    if db_path and data_to_push and user_id:
                        # Hier rufen Sie die synchrone Firebase-Push-Funktion auf.
                        # Dies ist eine blockierende Operation im Kontext dieses Threads.
                        # Der Thread gibt den GIL frei, während er auf die Netzwerk-Antwort wartet.
                        print(f"  Pushing data for user {user_id} to {db_path}...")
                        try:
                            # Annahme: _sync_push_local_change wurde wie zuvor definiert
                            # und nutzt das global initialisierte firebase_admin SDK
                            self._sync_push_local_change(db_path, data_to_push)
                            print(f"  Push erfolgreich.")
                        except Exception as e:
                            print(f"  Push FEHLER: {e}")
                        # Nachdem der Push abgeschlossen ist (egal ob Erfolg oder Fehler),
                        # kehrt die Ausführung hierher zurück, und der Thread kann die nächste Aufgabe holen.
                    else:
                        print(f"  FEHLER: Ungültige Daten für firebase_push Aufgabe: {task}")

                elif task_type == 'other_task':
                    print("  Verarbeite andere Aufgabe...")

                else:
                    print(f"  FEHLER: Unbekannter Aufgabentyp: {task_type}")

                # Wichtig: Signalisieren, dass die Aufgabe bearbeitet wurde
                q.task_done()

            except queue.Empty:
                # Tritt auf, wenn das Timeout in q.get erreicht wurde und die Queue leer war
                # Ist normal, allows checking for STOP_SIGNAL
                pass
            except Exception as e:
                print(
                    f"Worker Thread {threading.current_thread().name}: Unerwarteter Fehler bei Aufgabenverarbeitung: {e}")
                # In einer echten Anwendung müssten Sie hier entscheiden,
                # ob die Aufgabe als fehlerhaft markiert und q.task_done() trotzdem aufgerufen wird,
                # um ein Hängenbleiben zu verhindern.

        print(f"Worker Thread {threading.current_thread().name}: Beendet.")



    async def start_sim(self):
        """
        Startet die Simulationslogik in einem separaten Thread.
        Diese Funktion ist nicht-blockierend für den asyncio Event Loop.
        """
        print(f"Main Loop: Starte Simulations-Thread für User {self.user_id}, Env {self.env_id}")

        # Erstellen Sie einen Thread, der die _run_simulation_logic Methode ausführt
        simulation_thread = threading.Thread(
            target=self._run_simulation_logic,
            name=f"SimThread-{self.user_id}-{self.env_id}",  # Optional: Benennen Sie den Thread
            daemon=True  # Optional: Der Thread wird beendet, wenn das Hauptprogramm endet
        )

        # Starten Sie den Thread
        simulation_thread.start()

        print(f"Main Loop: Simulations-Thread gestartet. Kehre sofort zurück.")

        return True




    async def connect(self):
        query_string = self.scope["query_string"].decode()
        query_params = parse_qs(query_string)

        self.user_id = query_params.get("user_id", [None])[0]
        self.env_id = query_params.get("env_id", [None])[0]

        # todo improve auth
        if not self.user_id or not self.env_id:
            await self.close()
            return

        self.db_path = f"users/{self.user_id}/env/{self.env_id}"

        try:
            self.g = GGraphUtils(
                table_name="NONE",
                upload_to="fb",
                instance=os.environ.get("FIREBASE_RTDB"), # set root of db
                database=self.db_path, # spec user spec entry (like table)
                nx_only=False,
                G=None,
                g_from_path=None,
                user_id=self.user_id,
            )

            self.initial_data = self.g.firebase.get_data(self.db_path)

            if not self.initial_data:
                await self.close()
                return
        except Exception as e:
            logger.error(f"Firebase error: {e}")
            await self.close()
            return

        await self.accept()
        logger.info(f"WebSocket connection accepted for user {self.user_id}")

        # Init Sim





        # Start sim in sepparate thread
        await self.start_sim()

        self.qf_updator = QFUpdator(
            g=self.g,
            user_id=self.user_id,
            # Eventuell weitere Parameter für Firebase-Pfade im Updator
        )


        # Sende initiale Daten direkt nach dem Connect
        await self.send(text_data=json.dumps({
            "type": "initial_data",
            "data": self.initial_data
        }))


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








