import asyncio
import os

from bm.settings import TEST_USER_ID
from qf_sim.physics.quantum_fields.qf_updator import QFUpdator
from utils.graph.get_utils import get_graph_utils
from utils.simulator.world.create_world import CreateWorld
import threading


class SimCore:

    def __init__(self, g=None, env_id=None, env_c=None, user_id=TEST_USER_ID):
        self.g = g
        self.env_id = env_id
        self.env_c = env_c
        self.user_id = user_id


    def create(self, g_path, user_id, env_id, components, database):
        print("g_path, user_id, env_id", g_path, user_id, env_id)
        self.user_id = user_id
        self.env_id = env_id

        # validate needed Graph
        g_obj = get_graph_utils(
            local=True,
            user_id=user_id,
            env_id=env_id,
        )

        # create
        print("Create Graph")
        self.g = g_obj(
            upload_to="fb",
            database=database,
            nx_only=True,
            g_from_path=g_path,
            user_id=user_id,
            env_id=env_id,
        )

        if not os.path.exists(g_path):
            self.world_creator = CreateWorld(self.g, components, world_type="bare", user_id=self.user_id)
            self.env_c=asyncio.run(self.world_creator.hello_world())

        else:
            print("Graph already exists")


    def run(self):
        self.qf_updator = QFUpdator(
            g=self.g,
            user_id=self.user_id,
            env_id=self.env_id
            # Eventuell weitere Parameter für Firebase-Pfade im Updator
        )
        print(
            f"Thread {threading.current_thread().name}: Simulationslogik gestartet für User {self.user_id}, Env {self.env_id}")

        try:
            # run
            asyncio.run(self.qf_updator.update(self.env_id, self.env_c))
            print(
                f"Thread {threading.current_thread().name}: Simulationslogik abgeschlossen für User {self.user_id}, Env {self.env_id}")

        except Exception as e:
            print(f"Thread {threading.current_thread().name}: FEHLER in Simulationslogik: {e}")
