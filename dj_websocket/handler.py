import asyncio
import json

import websockets
from channels.layers import get_channel_layer

from bm.settings import WS_URL


class WebsocketHandler:
    """



    """

    def __init__(self,g):
        self.g=g

    async def distribute(
            self,
            data,
            node,
            message_handler,
            user_id=None,
            env=None
    ):
        tasks = [
            self.send_node(
                uri=f"{WS_URL}qf-sim/run/single/node_id={nid}/",
                user_id=user_id,
                env=env,
                message_handler=message_handler,
                # Sends loop item if no node provided
                node=node or {"id": nid, **attrs}
            )
            for nid, attrs in data
        ]
        responses = await asyncio.gather(*tasks)
        print("Done", responses)
        return

    async def send_node(self, uri, node, message_handler, user_id=None, env=None):
        neighbors = self.g.get_neighbor_list(node.get("id"), "QFN")

        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({
                "user_id": user_id,
                "env": env,
                "node": node,
                "neighbors": neighbors
            }))
            print("connection to", uri, "established")
            while True:
                msg = await websocket.recv()
                message_handler(msg)

    async def send_intern_message_pool(
            self,
            nid,
            trgt_node_id,
            data,
            msg_type="neighbor_update",
    ):
        channel_layer = get_channel_layer()
        await channel_layer.send(
            trgt_node_id,
            {
                "type": msg_type,
                "data": data,
                "key": nid,
                # todo secret key
            }
        )