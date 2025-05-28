import pprint

from utils.file.yyaml import load_yaml
from utils.simulator.world.env import ENV


class ENVCCreator:

    def __init__(self, g, user_id, world_type="bare"):
        self.world_type = "bare"
        self.content_base_path = r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env"

        self.content = self.validate_env_type()

        self.g = g
        self.user_id = user_id
        self.envc_id = f"env_{self.world_type}_{self.user_id}"
        self.layer="ENV"
        self.ion_count = 0

    def validate_env_type(self):
        env_content = None

        if self.world_type == "bare":
            # bare physics simulation
            env_content = ENV.copy()
        elif self.world_type == "cellular":
            # biophysic sim
            pass
        return env_content



    def create(self):
        """
        Create an ENVC layer (Environment Control Layer)
        which manages global fields like temperature, ions, etc.
        """
        print("Creating ENVC...")
        # todo customize settings -> read from received yaml -> incl tiemsteps
        self.content["id"] = self.envc_id
        env_c= dict(
                world_type=self.world_type,
                type=self.layer,
                parent=["USERS"],
                **self.content,
            )

        self.g.add_node(
            attrs=env_c
        )
        print("Node added", self.envc_id, self.g.G.nodes[self.content["id"]])

        print("Link USER to ENV")
        self.g.add_edge(
            src=self.user_id,
            trt=self.envc_id,
            attrs=dict(
                rel="has",
                src_layer="USERS",
                trgt_layer=self.layer
            )
        )

        return self.content["dim"], env_c


                    
