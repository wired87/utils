import asyncio
import os
from threading import Thread

import websockets
from fastapi import WebSocket

from utils.utils import Utils

class ConnectionManager:
    def __init__(self):
        self.all_ips_len = None
        local_origins = ["127.0.0.1", "localhost"]
        prod_origins =  ["bestbrain.tech"]
        self.request_urls = []
        self.allowed_origins = local_origins if os.name == "nt" else prod_origins
        self.active_connections = {}

        self.all_ready = False
        self.utils = Utils()
        self.all_authenticated = False
    async def connect(self, websocket: WebSocket, env_id):
        granted = await self._validate_origin(env_id, websocket)
        if granted and env_id not in self.active_connections:
            #
            self.active_connections[env_id] = websocket


    async def connect_cluster_ips(self, ip, pod_name):
        auth_payload= {
            "type": "auth",
            "data": {
                "key": pod_name
            }
        }
        try:
            endpoint = f"https://{ip}:8001/{pod_name}/"
            cr = await self.utils.apost(
                url=endpoint,
                data=auth_payload,
            )
            if cr and "response_key" in cr and "key" in cr and "session_id" in cr:
                if cr["key"] == pod_name:
                    # Successful pod authenticated -> append valid
                    self.active_connections[pod_name] = cr.update(
                        {"url": endpoint}
                    )

                    if len(self.all_ips_len) == len(list(self.active_connections.keys())):
                        self.all_authenticated = True

                    return pod_name
                else:
                    print(f"Invlalid key received: {cr['key']}")
            else:
                raise ValueError("No con request triger controlled Exceptio")
        except Exception as e:
            print(f"Error fetching: {e}")


    async def _validate_origin(self, env_id, websocket: WebSocket):
        print(f"validate received WS request to Host ")
        def validate_sender_url():
            ok = False
            for item in self.allowed_origins:
                if websocket.url.hostname.startswith(item):
                    ok=True
            return ok

        if validate_sender_url():
            print("connection accepted")
            await websocket.accept()
            return websocket.url.hostname
        else:
            print("connection declined")
            await websocket.close(code=1008)
            return None



    async def request_urls_process(self):
        print("Connnection request process started")
        try:
            # set len
            self.all_ips_len = list(self.all_ips.keys())
            while self.all_authenticated is False:
                if self.all_ready is True:
                    pod_id = None
                    for pod_name, ip in self.all_ips.items():
                        pod_id:str or None = await self.connect_cluster_ips(ip, pod_name)
                    if pod_id is not None:
                        self.all_ips.pop(pod_id)
                    pod_id = None
        except Exception as e:
            print(f"Error: {e}")
        print("Finished Connection request process")



    def start_connection_thread(self):
        # FB Upsert thread
        print("Create Con thread")

        def _connect():
            asyncio.run(
                self.request_urls_process()
            )

        self.con_thread = Thread(
            target=_connect,
            name="POD_INIT_CONNCTION",
            daemon=True  # Optional: Der Thread wird beendet, wenn das Hauptprogramm endet
        )

        # Start Thread
        self.con_thread.start()
        print("Connect to Pods thread started")

    def activate_spam_threads(self, all_ips):
        self.all_ips = all_ips
        if len(self.request_urls):
            self.start_connection_thread()






class WebsocketHandler:
    """
    """

    def __init__(self, uri):
        self.uri=uri
        print("WS handler initialized")

    async def establish_connection(self):
        try:
            print(f"Establish connection to {self.uri}")
            return websockets.connect(self.uri)
        except Exception as e:
            print("WS couldn't be established:", e)

