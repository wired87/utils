
import os

import websockets
from channels.layers import get_channel_layer

from fastapi import WebSocket

class ConnectionManager:
    def __init__(self, host_id="123"):
        self.host_id = host_id
        local_origins = ["127.0.0.1", "localhost"]
        prod_origins =  ["bestbrain.tech"]
        self.allowed_origins = local_origins if os.name == "nt" else prod_origins
        self.active_connections ={}

    async def connect(self, websocket: WebSocket, env_id):
        granted = await self._validate_origin(env_id, websocket)
        if granted and env_id not in self.active_connections:
            #
            self.active_connections[env_id] = websocket

    async def _validate_origin(self, env_id, websocket: WebSocket):
        print(f"validate received WS request to Host {self.host_id} ")
        def validate_sender_url():
            ok = False
            for item in self.allowed_origins:
                if websocket.url.hostname.startswith(item):
                    ok=True
            return ok

        if env_id == self.host_id and validate_sender_url():
            print("connection accepted")
            await websocket.accept()
            return websocket.url.hostname
        else:
            print("connection declined")
            await websocket.close(code=1008)
            return None



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

    async def send_intern_message_pool(
            self,
            nid,
            trgt_node_id,
            data,
            msg_type="neighbor_update",
            process_key=None,
    ):
        channel_layer = get_channel_layer()
        await channel_layer.send(
            trgt_node_id,
            {
                "type": msg_type,
                "data": data,
                "key": nid,
                "process_key": process_key
                # todo secret key
            }
        )