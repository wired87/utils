import json
import os

import networkx as nx
import numpy as np

from ggoogle.storage.storage import GBucket
from gnn import SRC_PATH
from utils.file import aread_json_content
from gnn.embedder import get_embedder
from utils.utils import GraphUtils


class TEmbedder:

    def __init__(self):
        self.bucket = GBucket("bestbrain")

    async def upload_embed_bucket(self, embeds, key):

        await self.bucket.upload_json_to_folder(
            bucket_path=f"{SRC_PATH['paths']['graph']['sne']['bucket']}/rag/",
            json_content={"embeds": embeds},
            file_name=f"{key}_embeds.json"
        )
    
    
    async def embed_query(self, query):
        return get_embedder().embed(query)
    
    async def transformer_embed_graph(
            self,
            G,
            nx_sne_bucket_path=SRC_PATH["paths"]["graph"]["sne"]["bucket"],
            key="go_term",
            t="gcp"
    ):
        bucket_folder = os.path.join(nx_sne_bucket_path, f"{key}_graph.json")
        print("bucket_folder", bucket_folder)
        """Indexes graph embeddings into Pinecone from a cloud storage bucket."""
        print("get from", bucket_folder)
        if not G or len(G.nodes()) == 0 or len(G.edges()) == 0:
            # Download graph
            G=nx.Graph()
            g_utils = GraphUtils(G=G, general_stuff=SRC_PATH)
            G = await g_utils.download_sne(bucket_folder)
        embeds = []
        for node_id, attrs in G.nodes(data=True):
            embed = get_embedder().encode(json.dumps(
                {
                    "id": node_id,
                    "data": {**attrs}
                }
            ))
            embeds.append(embed)
        for src, trt, attrs in G.edges(data=True):
            embed = embedder.encode(json.dumps(
                {
                    "source": src,
                    "target": trt,
                    "attrs": {**attrs}
                }
            ))
            embeds.append(embed)
        if t=="gcp":
            await self.upload_embed_bucket(embeds, key)
        else:
            upserter = VectorUpserter()
            pcvs = PCVectorStore()
            index = await  pcvs.aget_index(name="bestbrain")
            if index is None:
                return None
            upserter.upsert_pc(embeds=embeds, pinecone_index=index, namespace=key)
        print("Finished indexing graphs into Pinecone.")


    async def get_embedding_from_gcs(self, bucket_folder_path, key="go_term"):
        print("Fetch embeds fom gs")
        content = await self.bucket.download_single_file(
            download_as_string=True,
            prefix=bucket_folder_path,
            file_name=f"{key}_embeds.json"
        )
        if content:
            print("Embed Content retrieved successfully!")
            embeds = json.loads(content).get("embed", None)
            if not embeds:
                print("No embeds found in content")
                return None
            return np.array(embeds)
        return None


    async def load_local_embeds(self, local_path):
        content = await aread_json_content(local_path)
        if content:
            print("Local embeds found...")
            embed = content.get("embed")
            return np.array(embed)
        print(f"Local embed not found @ {local_path}")

    async def main(self, local_path, bucket_path, key, query, dj=None):
        if not dj:
            if not os.path.exists(local_path):
                embed = await self.get_embedding_from_gcs(bucket_path, key)
            else:
                embed = await self.load_local_embeds(local_path)
        else:
            embed = None # uery embs from global multiprocessing.Manager
        return embed





