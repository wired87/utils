import json


def deserialize(world_cfg):
    if isinstance(world_cfg, str):
        world_cfg = json.loads(world_cfg)
    return world_cfg
