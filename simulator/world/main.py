import asyncio
import json

import networkx as nx

from utils.utils import GraphUtils
from utils.simulator.world.create_world import CreateWorld, WorldCore
from utils.simulator.world.run_world import World

GP = r"C:\Users\wired\OneDrive\Desktop\Projects\bm\bm_process\world\world01.json"

def create():
    world_core = WorldCore()

    god = CreateWorld(world_core.g_utils, world_core.user_id)
    asyncio.run(god.hello_world())

    with open(GP, "w") as f:
        json.dump(nx.node_link_data(world_core.g_utils.G), f)


def run():
    G=None
    with open(GP) as f:
        data = json.load(f)
        G = nx.node_link_graph(data)

    g_utils=GraphUtils(
        G=G,

    )

    world = World(
        g_utils
    )
    world.run()

if __name__ == "__main__":
    create()
    run()


