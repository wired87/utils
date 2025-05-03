"""
Adapted layer save method
Include embeddings in add_x
swap add_x calls
test model
handle protien&gene
organoids
improve goterm, gocam, reactome
gene variants
gene regualtory/non-coding -> GENCODE
handle self.G better (currently you just once set it in all classes - means,
-> if you update it in class A there are no changes in child class B

process membrane fluctuation (controlled fire
Single-Cell Multi-Omics Data (scRNA-seq, scATAC-seq, CITE-seq) → Captures gene expression & regulatory states.

We need ATAC-seq, ChIP-seq, and Hi-C data to link gene activity to non-coding DNA.
Cell Morphology Data (CellProfiler, Allen Cell Explorer) → Provides structural features.
Protein Interaction Networks (STRING, BioGRID) → Encodes protein relationships.
enformer  for expression prediction of identified transcript

gnn-project harvard 40gb data


Mach die graph transformer pipe fertig

todo:
- build repair
- script debug


"""
import os

import networkx as nx

from utils.aws.process_ensembl import aread_json_content
from _google.storage import MOUNT_PATH, MAIN_BUCKET
from _google.storage.storage import GBucket
from utils.utils import Utils

#from gnn.processing.layer.main import LayerProcessor

TDATA_PATH = "train_data/" if os.name == "nt" else os.path.join(MOUNT_PATH, MAIN_BUCKET, "train_data")
TEST_WEB_URL = "https://www.encodeproject.org/report/?type=Experiment&status=released&control_type%21=%2A&replicates.library.biosample.donor.organism.scientific_name=Homo+sapiens&biosample_ontology.organ_slims=brain&limit=all"
NX_GRAPHS = [
    {
        "layer": "gene",
        "parent": ["species", "human_gene"],
        "url": "train_data/gene/ensembl_9606.json",
        "local": r"C:\Users\wired\OneDrive\Desktop\Projects\bm\data\main_ckpt\gene.json"
    },
    {
        "layer": "cell_line",
        "parent": ["encode", "cell", "experiment"],
        "url": r"C:\Users\wired\OneDrive\Desktop\Projects\bm\data\extractors\functions\encode\cell_line_processor\metadata.tsv",
    },


    {
        "layer": "human_protein",
        "parent": ["protein", "human_gene"],
        "url": "train_data/protein/uniprot_9606.json",
    },
    {
        "layer": "brain_experiment",
        "parent": ["encode"],
        "url": TEST_WEB_URL,
    }, {
        "layer": "ECO",
        "parent": ["ontology"],
        "url": "train_data/evidence/eco.json",
    },
    {
        "layer": "gocam",
        "parent": ["gene"],
        "url": "train_data/interaction_pathways/gocam.json",
    }, {
        "layer": "reactome",
        "parent": ["pathway", "gene", "interaction"],
        "url": "train_data/interaction_pathways/reactome.json",
    },



    ################
{
        "layer": "RO",
        "parent": ["ontology"],
        "url": r"https://raw.githubusercontent.com/oborel/obo-relations/master/ro.obo",
    },
{
        "layer": "GO",
        "parent": ["ontology", "gene"],
        "url": r"train_data/ontology/gene_ontology.json",
    },{
        "layer": "cell_transcriptomes",
        "parent": ["cell"],
        "url": "train_data/cell/transcriptomes/thalamic_6k_9606.json",
    },
]


class GraphHandler:
    """
    - check sne already exists
    DO NOT USE NX. CONVRT IN ONE RUN
    """

    def __init__(self, bucket_name="bestbrain"):
        self.G = nx.Graph()
        self.success_list = []
        self.bucket = GBucket(bucket_name)
        self.utils = Utils()

        self.lp = None
        self.batch_size = 100
        self.batch_state = 0




    async def _list_layer_blobs(self):
        bucket_blobs = self.bucket.list_bucket_objects()
        for bblob in bucket_blobs:
            if bblob.name == "layer/":
                processed_layer_blobs = self.bucket.client.list_blobs("bestbrain", prefix=bblob.name)
                if len(processed_layer_blobs) > 0:
                    for lblob in processed_layer_blobs:
                        if lblob.name == "all.json":
                            print("All layers processed...")
                            return lblob
                    return processed_layer_blobs
        return []

    async def process_layers(self, key, item):
        """
        ToDO check extend layer
        """
        # 1. CHECK FOR SAVED G -> MERGE
        self.utils = Utils()
        ckpt = await self.utils.check_ckpt(key=item["path"])
        if ckpt:
            print("🔹 Merge Graph")
            self.G = ckpt
            print("ckpt type:", type(self.G))  # Debugging: Check what ckpt is
            print("ckpt nodes:", len(self.G.nodes()) if isinstance(ckpt, nx.Graph) else "Not a Graph")
            print("ckpt edges:", len(self.G.edges()) if isinstance(ckpt, nx.Graph) else "Not a Graph")
            print("Reinit helper classes")

            self.utils = Utils()
            self.lp = None
            return
        tran_data_dest_path = None
        dest_path = await self.utils.get_train_data(
            key=item["path"],  # e.g. ensembbl.json
            dest_path=tran_data_dest_path,
            prefix=""  # self.general_stuff["paths"]["train_data"]["bucket"]
        )

        if not dest_path:
            return

        data = await aread_json_content(dest_path)
        if key == "gene":
            data = data["genes"]
        elif key == "protein":
            data = data["results"]
        await self.lp.process_layer(data, key)
        data = None
        print(f"Layer {key} processed")
        self.success_list.append(key)






    async def main(self, mvp=True):
        print("Working MVP layers")
        await self.mvp_handler(mvp)
        print("done")


    async def mvp_handler(self, mvp):
        if mvp:
            print("Extract tree...")
            for item in NX_GRAPHS:
                if item["url"].startswith("http"):
                    content = await self.utils.download_json_content(
                        item["url"],
                        j=True if item["layer"] != "RO" else False,
                        save=True
                    )
                else:
                    content = await self.load_content(
                        path=item["url"],
                        single=False,
                        layer=item["layer"],
                        local=item.get("local"),
                    )
                await self.lp.process_layer(content, layer=item["layer"], parent=item["parent"])
                content = None
