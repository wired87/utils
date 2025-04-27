

"""
Possible input attrs( all of these attributes or none of them )
a: the adjacency matrix
x: the node features
e: the edge features
y: the labels

tech
GNN - PyG https://pytorch-geometric.readthedocs.io/en/latest/
sne =


MARK: ALLTIES / BEFOR FILENAME

"""
import os
from pathlib import Path

OS_NAME = os.name
BASE=r"C:\Users\wired\OneDrive\Desktop\Projects\bm" if OS_NAME == "nt" else "./"
LOCAL_LAYERS = rf"{BASE}\uutils\gnn\model\layer\all_layers_custom.json"
L_NX_GRAPH = rf"{BASE}\data\main_ckpt\nx\graph.json" if OS_NAME == "nt" else "data/model_graph/nx/graph.json"
HETERO_PATH = rf"{BASE}\data\main_ckpt\hetero\graph.pt" if OS_NAME == "nt" else "data/main_ckpt/hetero/graph.pt"
L_NX_GRAPH_EMBED = rf"{BASE}\main_ckpt\g_embed" if OS_NAME == "nt" else "data/main_ckpt/g_embed"


NX_BUCKET_CKPT = Path("model_graph/sne/")
NX_LOCAL_CKPT = rf"{BASE}\main_ckpt\sne" if OS_NAME == "nt" else "data/model_graph/sne/"


L_MODEL_CKPT = rf"{BASE}\data\main_ckpt\model" if OS_NAME == "nt" else "data/main_ckpt/model"
B_MODEL_CKPT = "data/model_graph/model_ckpt/"

SNE_DIR_L_NX = Path(r"data\main_ckpt\sne")

GCS_GRAPH_CKPT="/model_graph"

LRAW_DATA = rf"{BASE}\data\raw" if OS_NAME == "nt" else "data/raw/"
BRAW_DATA ="model_graph/train_data/raw/"

ACTION = {
    "graph": {
        "create": True,
        "add": False,
        "merge": False,
    },
    "model": {
        "train": False,
        "test": False,
        "type": "gt"  # sage | han | gtm | rag
    },
    "rag": {
        "create": False,
        "test": False,
    }
}
# todo mount bucket vol. -> you just need a single file url

SRC_PATH = {
    "raw_graph_data_bucket": "train_data/",
    "raw_graph_data_local": "./data/train_data/",

    "pre_graph_data_bucket": "train_data/",
    "pre_graph_data_local": "./data/train_data/",

    "nx_bucket": "model_graph/sne",
    "nx_local": SNE_DIR_L_NX,
}


r"""

    "data": {
        "experiment": {
            "path": ["https://www.encodeproject.org/report/?type=Experiment&status=released&control_type%21=%2A&replicates.library.biosample.donor.organism.scientific_name=Homo+sapiens&biosample_ontology.organ_slims=brain&limit=all"],
            "train": True,
            "merge": False,
        },
        "gene_ontology": {
            # go-plus many chebi entries
            "path": "go-plus.json",
            "train": True,
            "merge": False,
        },
        "eco": {
            "path": "eco.json",
            "train": False,
            "merge": False,

        },
        "reactome": {
            "path": "reactome_detail.json",
            "train": True ,
            "merge": False,
        },
        "cell": {
            "path": "ALL.json",
            "train": True,
            "merge": False,
        },
        "gocam": {
            "path": "list_gocams.json",
            "train": True,
            "merge": False,
        },
        "protein": {
            "path": "uniprotkb_9606.json",
            "train": True,
            "merge": False,
        },
        "gene": {
            "path": "ensemble.json",
            "train": True,
            "merge": False,
        },

        "relation_ontology": {
            # TODO: chekc for exisiting node before set (maybe set already in GOterm edges
            # from ro to X relationship=relationship_destination
            # from X to ro relationship=src_relationship
            "path": "RO.json",
            "train": False,

        },
        "chebi": {
            # many nodes already created in goterm
            "path": ".json",
            "train": False,

        },
        "cell_organoids": {
            "path": [
                "https://explore.data.humancellatlas.org/projects/005d611a-14d5-4fbf-846e-571a1f874f70/get-curl-command"],
            "train": False,
            "merge": False,

        },
        "components": {
            "path": r"C:\Users\wired\Desktop\demo_raw_c2\src\app\(site)",
            "train": False,
            "merge": False,
        },
        "sites": {
            "path": r"C:\Users\wired\Desktop\demo_raw_c2\src\components",
            "train": False,
            "merge": False,
        },
        "ontology": {
            "path": [
                "https://ftp.ebi.ac.uk/pub/databases/spot/ols/latest/ontologies_linked.json.gz"],
            "train": False,
            "merge": False,
        },
        "free_mode": {
            "path": [
                "https://ftp.ebi.ac.uk/pub/databases/spot/ols/latest/ontologies_linked.json.gz"],
            "train": False,
            "merge": False,
        },
    },
"""








