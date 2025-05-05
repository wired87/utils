from bm_process.ecm import TEMPC


class TemperatureCreator:

    def __init__(self, env_id, g_utils):
        self.g_utils=g_utils
        self.env_id=env_id
        self.layer="TEMPERATURE_FIELD"

    def create(
            self,
            src_layer="ENV"
    ):
        item = TEMPC.copy()
        item["id"] = f"{TEMPC['id']}_{self.env_id}"
        self.g_utils.add_node(
            attrs=dict(
                weight=1,
                **item,
            ),
        )
        self.g_utils.add_edge(
            src=self.env_id,
            trt=item["id"],
            attrs=dict(
                rel="has",
                src_layer=src_layer.upper(),
                trgt_layer=self.layer
            ),
        )
