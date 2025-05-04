from physics import ENVC

content = ENVC.copy()
class ENVCCreator:

    def __init__(self, g, user_id):
        self.g_utils = g
        self.user_id = user_id
        self.envc_id = f"env_{self.user_id}"
        self.layer="ENV"
        self.ion_count = 0


    def create(self):
        """
        Create an ENVC layer (Environment Control Layer)
        which manages global fields like temperature, ions, etc.
        """

        print("Creating ENVC...")
        content["id"] = self.envc_id
        self.g_utils.add_node(
            attrs=dict(
                type=self.layer,
                parent=[self.user_id],
                **content
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

