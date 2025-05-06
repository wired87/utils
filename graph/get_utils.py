def get_graph_utils(local=True, **kwargs):
    if not local:
        from _google.graph.g_utils import GGraphUtils
        # loads both GGraphUtils and LocalGraphUtils
        base = GGraphUtils
    else:
        from utils.graph.local_graph_utils import LocalGraphUtils
        base = LocalGraphUtils

    class GraphUtils(base):
        def __init__(self, **init_kwargs):
            super().__init__(**kwargs if not init_kwargs else init_kwargs)
            print("init Gutils")

        def custom_method(self):
            print("Extra stuff")

    return GraphUtils
