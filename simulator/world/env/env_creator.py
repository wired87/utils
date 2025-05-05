import os

from utils.file.yaml import load_yaml


class ENVCCreator:

    def __init__(self, g, user_id, world_type="bare"):
        self.world_type = "bare"
        self.content_base_path = r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env"

        self.content = self.validate_env_type()
        self.g_utils = g
        self.user_id = user_id
        self.envc_id = f"env_{self.world_type}_{self.user_id}"
        self.layer="ENV"
        self.ion_count = 0

    def validate_env_type(self):
        if self.world_type == "bare":
            # bare physics simulation
            ENV_PATH = os.path.join(self.content_base_path, "bare_env.yaml")
        elif self.world_type == "cellular":
            # biophysic sim
            ENV_PATH = os.path.join(self.content_base_path, "cellular_env.yaml")
        return load_yaml(ENV_PATH)

    def create(self):
        """
        Create an ENVC layer (Environment Control Layer)
        which manages global fields like temperature, ions, etc.
        """
        print("Creating ENVC...")
        self.content["id"] = self.envc_id
        self.g_utils.add_node(
            attrs=dict(
                world_type=self.world_type,
                type=self.layer,
                parent=[self.user_id],
                **self.content
            ),
        )
        print("Link USER to ENV")
        self.g_utils.add_edge(
            src=self.user_id,
            trt=self.envc_id,
            attrs=dict(
                rel="has",
                src_layer="USERS",
                trgt_layer=self.layer
            ),
        )
        return self.envc_id

