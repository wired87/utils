import pprint
#from _google.spanner.acore import SpannerAsyncHelper
from utils.simulator.world.create_world import WorldCore


class WorldObjectLoader(
    #SpannerAsyncHelper,
    WorldCore
):

    def __init__(self, g, user_id, env_id, local_g_path):
        super().__init__()
        self.g = g
        self.user_id = user_id
        self.env_id = env_id

        self.win_size = None
        self.ion_types = None
        self.env_cell_ids = None
        self.membranes = None
        self.testing = True  #-> get from BQ
        self.local_g_path = local_g_path

    async def load_local_graph(self):

        if self.testing is False:
            print("Load graph")
            # Get ENV entry from BQ
            query=self.g.get_entry_from_table_query(
                table="ENV",
                value_of_interest=self.env_id,
                key_of_interest="id"
            )
            env:dict = self.g.run_query(query, conv_to_dict=True)[0]

            # Load local NXG
            self.g.add_node(env)

            query = self.g.entry_from_parent_entry_query(
                table="PARTICLE",
                parent_entry=self.env_id,
            )

            particle_entries: list[dict] = self.g.run_query(query, conv_to_dict=True)

            # Load local NXG
            for particle in particle_entries:
                self.g.add_node(particle)

            self.g.print_status()
            print("Finished local loading")
            return

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