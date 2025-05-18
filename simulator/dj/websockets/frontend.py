import asyncio
import logging
import os



import threading

from channels.generic.websocket import AsyncWebsocketConsumer

from _google.graph.g_utils import GGraphUtils
from physics.quantum_fields.qf_updator import QFUpdator
from urllib.parse import parse_qs

import json
logger = logging.getLogger(__name__)

class SimulationWebsocket(AsyncWebsocketConsumer):
    """
    Start- and update Entry for each sim.




    - Load Graph data from firebase and convert
        - ceate thread and run the sim (update -> each update push to fb)
    """

    async def connect(self):
        query_string = self.scope["query_string"].decode()
        query_params = parse_qs(query_string)

        self.user_id = query_params.get("user_id", [None])[0]
        self.env_id = query_params.get("env_id", [None])[0]
        # todo collect more sim data like len, elements, ...

        # todo improve auth
        if not self.user_id or not self.env_id:
            await self.close()
            return

        self.db_path = f"users/{self.user_id}/env/{self.env_id}"

        try:
            self.g = GGraphUtils(
                table_name="NONE",
                upload_to="fb",
                instance=os.environ.get("FIREBASE_RTDB"),  # set root of db
                database=self.db_path,  # spec user spec entry (like table)
                nx_only=False,
                G=None,
                g_from_path=None,
                user_id=self.user_id,
            )

            # Load Graph data from firebase and convert
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

        # Sende initiale Daten direkt nach dem Connect
        await self.send(text_data=json.dumps({
            "type": "initial_data",
            "data": self.initial_data
        }))


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







    async def start_sim(self):
        """
        Startet die Simulationslogik in einem separaten Thread.
        Diese Funktion ist nicht-blockierend für den asyncio Event Loop.
        """
        print(f"Main Loop: Starte Simulations-Thread für User {self.user_id}, Env {self.env_id}")

        # Erstellen Sie einen Thread, der die _run_simulation_logic Methode ausführt
        simulation_thread = threading.Thread(
            target=self._run_simulation,
            name=f"SimThread-{self.user_id}-{self.env_id}",  # Optional: Benennen Sie den Thread
            daemon=True  # Optional: Der Thread wird beendet, wenn das Hauptprogramm endet
        )

        # FB Upsert thread
        upsert_thread = threading.Thread(
            target=self.g.q_handler.working_queue,
            name=f"UpsertThread-{self.user_id}-{self.env_id}",  # Optional: Benennen Sie den Thread
            daemon=True  # Optional: Der Thread wird beendet, wenn das Hauptprogramm endet
        )

        # Start Thread
        simulation_thread.start()
        upsert_thread.start()

        print(f"Main Loop: Simulations-Thread gestartet. Kehre sofort zurück.")
        return True

    def _run_simulation(self):

        self.qf_updator = QFUpdator(
            g=self.g,
            user_id=self.user_id,
            # Eventuell weitere Parameter für Firebase-Pfade im Updator
        )
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

