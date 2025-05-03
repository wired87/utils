"""
pip install torch torch-geometric _google-cloud-storage networkx


"""



import os
import json
import torch
import networkx as nx
from google.cloud import storage
from torch_geometric.nn import TransformerConv

# Configure Google Cloud Storage
BUCKET_NAME = "bestbrain"
LOCAL_MODEL_DIR = "./model_graph"
os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)


class GraphTransformer(torch.nn.Module):
    """Basic Graph Transformer Model"""

    def __init__(self, in_channels, out_channels):
        super(GraphTransformer, self).__init__()
        self.conv1 = TransformerConv(in_channels, 128, heads=4, concat=True)
        self.conv2 = TransformerConv(128 * 4, out_channels, heads=4, concat=False)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index)
        return x


def load_graph_from_gcs(blob_name):
    """Download graph file from GCS and return NetworkX graph"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    local_file = os.path.join(LOCAL_MODEL_DIR, blob_name)
    blob.download_to_filename(local_file)

    with open(local_file, "r") as f:
        graph_data = json.load(f)

    G = nx.Graph()
    for node in graph_data["nodes"]:
        G.add_node(node["id"], **node)
    for edge in graph_data["edges"]:
        G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1.0))

    return G


def train_graph_transformer(G):
    """Converts NetworkX graph to PyTorch Geometric format and trains Transformer"""
    node_ids = list(G.nodes())
    node_mapping = {node: i for i, node in enumerate(node_ids)}

    edge_index = torch.tensor(
        [[node_mapping[e[0]], node_mapping[e[1]]] for e in G.edges()],
        dtype=torch.long
    ).t().contiguous()

    node_features = torch.rand(len(node_ids), 16)  # Dummy features
    model = GraphTransformer(in_channels=16, out_channels=8)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    for epoch in range(10):
        optimizer.zero_grad()
        out = model(node_features, edge_index)
        loss = torch.nn.functional.mse_loss(out, node_features)
        loss.backward()
        optimizer.step()
        print(f"Epoch {epoch + 1}: Loss={loss.item()}")

    return model


def save_and_upload_model(model, blob_name):
    """Save trained model locally and upload to GCS"""
    local_model_path = os.path.join(LOCAL_MODEL_DIR, blob_name + ".pt")
    torch.save(model.state_dict(), local_model_path)

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob("trained_models/" + blob_name + ".pt")
    blob.upload_from_filename(local_model_path)

    print(f"✅ Model uploaded to GCS: gs://{BUCKET_NAME}/trained_models/{blob_name}.pt")


def main():
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    blobs = bucket.list_blobs(prefix="graphs/")  # Fetch graph files from GCS
    for blob in blobs:
        if blob.name.endswith(".json"):
            print(f"Processing {blob.name}")
            G = load_graph_from_gcs(blob.name)
            trained_model = train_graph_transformer(G)
            save_and_upload_model(trained_model, blob.name.replace(".json", ""))


if __name__ == "__main__":
    main()
