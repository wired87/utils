import pprint

from bm.settings import TEST_USER_ID
from _google.spanner.acore import SpannerAsyncHelper
from utils.world.create_world import WorldCore


class WorldObjectLoader(SpannerAsyncHelper, WorldCore):
    
    def __init__(self):
        super().__init__()
        self.user_id = TEST_USER_ID
        self.win_size = None
        self.ion_types = None
        self.env_id = f'env_{self.user_id}'
        self.env_cell_ids = None
        self.membranes = None



    async def get_env(self):
        # Get Env
        query =f"""
        SELECT * FROM ENV WHERE id = {self.env_id}
        """
        data:dict = await self.asnap(query=query, return_as_dict=True)
        self.g_utils.G.add_node(data)

        #Get neighbors
        query = f"""
        QUERY GRAPH {self.graph_name}
        MATCH (env:ENV)-[r]-(neighbor)
        WHERE env.id = '{self.env_id}'
        RETURN neighbor;
        """

        data:dict = await self.asnap(query=query, return_as_dict=True)
        print("Get ENV Neighbors")
        pprint.pp(data)
        for k, v in data.items():
            self.g_utils.G.add_node(v)
            if v["type"] == "CELL":
                self.g_utils.G.add_edge(self.env_id, v["id"], attrs=dict(rel="has"))
            elif v["type"] in self.ion_types:
                self.g_utils.G.add_edge(self.env_id, v["id"], attrs=dict(rel="has"))
            else:
                print("Skipping item", k, v)




    async def get_cells(self):
        for node_id, attrs in self.g_utils.G.nodes(data=True):
            if attrs.get("type") == "CELL":
                try:
                    query = f"""
                            QUERY GRAPH {self.graph_name}
                            MATCH (cell:CELL)-[r]-(neighbor)
                            WHERE cell.id = '{node_id}'
                            RETURN neighbor;
                            """
                    data: dict = await self.asnap(query=query, return_as_dict=True)
                    for k,v in data.items():
                        if v["type"] == "CELL":
                            self.g_utils.G.add_edge(node_id, v["id"], attrs=dict(rel=v["rel"]))
                        elif v["type"] in self.ion_types:
                            self.g_utils.G.add_edge(node_id, v["id"], attrs=dict(rel=v["rel"]))
                        elif v["type"] == "MEMBRANE":
                            self.g_utils.G.add_edge(node_id, v["id"], attrs=dict(rel=v["rel"]))
                except Exception as e:
                    print("Error getting cells", e)


    async def get_membranes(self):
        get_membrane_ids_from_edge_query=""
        for cell_id in self.env_cell_ids:
            get_membrane_ids_from_edge_query += f"""
            SELECT trgt FROM CELL_has_MEMBRANE WHERE src = '{cell_id}'
            """
        data: dict = await self.asnap(query=get_membrane_ids_from_edge_query, return_as_dict=True)

        membraine_query = ""
        for mem_id in data.values():
            membraine_query += f"""
            SELECT * FROM MEMBRANE WHERE id = '{mem_id}'
            """

        data: dict = await self.asnap(query=membraine_query, return_as_dict=True)
        self.membranes = data

    async def save_graph_ckpt(self):
        return

    async def load_objects(self):
        await self.acreate_session()
        await self.get_env()
        await self.get_cells()



if __name__ == "__main__":
    pass