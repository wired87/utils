import asyncio

import os

#daphne bm.asgi:application

import threading
import time

import networkx as nx
from channels.generic.websocket import AsyncWebsocketConsumer

from _google.firebase.real_time_database import FirebaseRTDBManager
from _google.graph.g_utils import GGraphUtils

from urllib.parse import parse_qs

import json

from physics.putils.calculator_creator import CalcCreator
from utils.logger import LOGGER
from utils.simulator.test import SimCore
from utils.utils import Utils
GRAPH_URL=""#

class SimulationWebsocket(AsyncWebsocketConsumer):
    """
    Get single node data Process in multithread and upload directly to DB.
    """
    testing=True
    utils = Utils()

    sim_paths = [
        "QF",
        "QFN",
        "ENV",
        "edges",
        #"PARTICLE"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.calc_creator = None
        self.run = True
        self.db_base = None
        self.sim = SimCore()

    async def connect(self):
        query_string = self.scope["query_string"].decode()
        query_params = parse_qs(query_string)

        self.user_id = query_params.get("user_id", None)[0]
        self.env_id = query_params.get("env_id", None)[0]

        # Receive sigle QFN
        self.node = query_params.get("node", None)[0]
        # check data validity
        if not self.node or not self.user_id or not self.env_id: # todo
            await self.close()
            return

        self.db_base = f"users/{self.user_id}/env/{self.env_id}/"

        # Case, User continues existing session -> If new session: run_session_id = None
        self.run_session_id = query_params.get("run_session_id", None)


        if self.run_session_id is None:
            # Create new session node
            self.run_session_id = f"session_{time.time()}".replace('.','_')
            self.db_path = f"{self.db_base}/session/{self.run_session_id}/"

        else:
            self.db_path = f"{self.db_base}/session/{self.run_session_id}"

            # Load Graph data from firebase and convert
        firebase = FirebaseRTDBManager(base_path=self.db_path)

        # todo fetch neighbors from either spanner or backend01 -> still build threre initial graph

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


        except Exception as e:
            LOGGER.error(f"Firebase error: {e}")
            await self.close()
            return

        await self.accept()
        LOGGER.info(f"WebSocket connection accepted for user {self.user_id}")

        # Build G and load in self.g
        env_attrs, env_id = self._build_inittial_G()

        # Init Sim
        self.loop = asyncio.get_event_loop()

        self.calc_creator = CalcCreator(self.g)

        # Start sim in sepparate thread
        # todo bei batch processing (einzelne qfns || ferm, higgs usw) in sepparate threads aufteilen
        await self.start_threads(env_attrs, env_id)

        # todo filter data before sending
        await self.send(text_data=json.dumps({
            "type": "initial_data",
            "message": "success",
            "data": json.dumps(nx.node_link_data(self.frontend_graph.G), indent=2)
        }))
        self.frontend_graph= None
    # jde zahl hat einen zustand das und die des nachbarn definiert den operator. es muss eine faustregel geben welche operatoren für zustände festlegt (zB "eine 5 und eine 6 ist immer + (alles in mathe ist letzendlich + oder -  ( evtl nicht wichtig -> auf interaktionen zwischenn paaren konzentireren"

    async def start_loop(self):
        print("Start loop")
        while self.run:
            await asyncio.gather(*[
                self.utils.apost(url=GRAPH_URL, data=node_id_data)
                for node_type, node_id_data in self.initial_data.items()
            ])

    def _build_inittial_G(self):
        # --- Graph aufbauen ---
        #print(f"Thread {threading.current_thread().name}: Baue Graph auf. Daten:", self.initial_data)
        env_attrs = None
        env_id = None

        #show = True
        #show2 = True
        print("self.initial_data.keys()", self.initial_data.keys())

        for node_type, node_id_data in self.initial_data.items():
            """if show == True and node_type == "QF":
                print("1111 nid, attrs", node_id_data)
                show = False"""
            print("node_type,", node_type)
            self.create_quantum_fields()
        return env_attrs, env_id



    async def start_threads(self, env_attrs, env_id):
        """
        Startet die Simulationslogik in einem separaten Thread.
        Diese Funktion ist nicht-blockierend für den asyncio Event Loop.
        """
        print(f"Main Loop: Starte Simulations-Thread für User {self.user_id}, Env {self.env_id}")

        # Erstellen Sie einen Thread, der die _run_simulation_logic Methode ausführt
        simulation_thread = threading.Thread(
            target=self.sim.run,
            name=f"SimThread-{self.user_id}-{self.env_id}",  # Optional: Benennen Sie den Thread
            daemon=True,  # Optional: Der Thread wird beendet, wenn das Hauptprogramm endet
            args =(env_attrs, env_id)
        )

        """# FB Upsert thread
        upsert_thread = threading.Thread(
            target=self.g.q_handler.working_queue,
            name=f"UpsertThread-{self.user_id}-{self.env_id}",  # Optional: Benennen Sie den Thread
            daemon=True  # Optional: Der Thread wird beendet, wenn das Hauptprogramm endet
        )"""

        # Start Thread
        simulation_thread.start()
        #upsert_thread.start()

        print(f"Main Loop: Simulations-Thread gestartet. Kehre sofort zurück.")
        return True




    async def disconnect(self, close_code):
        """Called when the websocket is disconnected."""
        LOGGER.info(f"WebSocket disconnected with code: {close_code}")
        # Cancel the simulation task when the client disconnects
        if hasattr(self, 'simulation_task'):
            self.simulation_task.cancel()
            try:
                await self.simulation_task # Wait for cancellation to complete
            except asyncio.CancelledError:
                LOGGER.info("Simulation loop task cancelled.")
        pass

    async def receive(self, text_data=None, bytes_data=None):
        LOGGER.info(f"Received message from frontend: {text_data}")
        try:
            data = json.loads(text_data)
            data_type = data.get("type")  # assuming 'type' field for command


            if data_type == "stim":

                LOGGER.info(f"Frontend command 'stimulus' added to queue.")
            elif data_type == "pause":
                # todo later
                LOGGER.info(f"Frontend command 'pause' added to queue.")
            elif data_type == "resume":
                # todo later
                LOGGER.info(f"Frontend command 'resume' added to queue.")
            elif data_type == "stop":
                # save logik
                # bye
                LOGGER.info(f"Frontend command 'stop' added to queue.")
            # Add more command types as needed
            else:
                LOGGER.warning(f"Unknown command type received: {data_type}")

        except json.JSONDecodeError:
            LOGGER.error(f"Failed to decode JSON from frontend: {text_data}")
        except Exception as e:
            LOGGER.error(f"Error processing received message: {e}")



