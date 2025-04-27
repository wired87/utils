"""
Epoch 30/30, Loss: 0.0045
"""

from pathlib import Path

import torch.nn as nn
import torch.optim as optim
from collections import defaultdict

import networkx as nx
import torch
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from google.cloud import storage
import os

from ggoogle.storage.storage import GBucket
from utils.utils import Utils


class GraphSAGETrainer:
    """Trainer for GraphSAGE"""

    def __init__(self,
                 G: nx.Graph,
                 layers,
                 info,
                 embedding_dim=128,
                 hidden_dim=64,
                 num_layers=2,
                 sample_neighbors=10,
                 epochs=10,
                 ):
        self.G = G
        self.embedding_dim = embedding_dim
        self.epochs = epochs
        self.sample_neighbors = sample_neighbors

        self.layers=layers
        self.info=info
        self.model_path = self.info['paths']['model']

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.node_features, self.adjacency_matrices = self._process_graph(G)
        self.bucket = GBucket("bestbrain")
        self.utils = Utils()
        # Initialize model
        self.model = GraphSAGEModel(embedding_dim, hidden_dim, embedding_dim, num_layers, sample_neighbors).to(
            self.device)

    def _process_graph(self, G):
        """Extracts node features and adjacency matrices efficiently from networkx.Graph"""
        node_mapping = {node: idx for idx, node in enumerate(G.nodes())}
        num_nodes = len(G)

        node_features = torch.randn(num_nodes, self.embedding_dim, device=self.device)
        node_features = torch.nn.functional.normalize(node_features, dim=1)

        adjacency_matrices = defaultdict(lambda: ([], []))

        for u, v, data in G.edges(data=True):
            rel = str(data.get("relationship", "interacts") or "interacts")
            if u in node_mapping and v in node_mapping:
                adjacency_matrices[rel][0].append(node_mapping[u])
                adjacency_matrices[rel][1].append(node_mapping[v])

        sparse_matrices = {
            rel: torch.sparse_coo_tensor(
                torch.tensor([src, dst], dtype=torch.long, device=self.device),
                torch.ones(len(src), dtype=torch.float, device=self.device),
                (num_nodes, num_nodes),
                dtype=torch.float32
            ).coalesce()
            for rel, (src, dst) in adjacency_matrices.items()
        }

        return node_features, sparse_matrices

    def train(self):
        """Train GraphSAGE with detailed logging"""
        self.model.train()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        loss_fn = nn.CosineEmbeddingLoss()

        batch_size = 5000
        for epoch in range(self.epochs):
            total_loss = 0
            num_batches = (len(self.node_features) + batch_size - 1) // batch_size

            for batch_idx in range(num_batches):
                start = batch_idx * batch_size
                end = min(start + batch_size, len(self.node_features))

                batch_features = self.node_features[start:end]
                batch_outputs = self.model(batch_features, self.adjacency_matrices)

                labels = torch.ones(batch_features.shape[0], device=self.device)
                loss = loss_fn(batch_outputs, batch_features, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                print(f"🔹 Batch {batch_idx + 1}/{num_batches} - Loss: {loss.item():.4f}")

            avg_loss = total_loss / num_batches
            print(f"🚀 Epoch {epoch + 1}/{self.epochs}, Avg Loss: {avg_loss:.4f}")

        self.save_model()


    def save_model(self):
        """Save trained model and upload to the bucket"""
        # Ensure local directory exists
        os.makedirs(os.path.dirname(self.model_path['local']), exist_ok=True)

        # Generate file name based on layers
        file_name = "SAGE" + "_".join(s for s in self.layers) + ".pth"

        # Define local and bucket paths
        local_path = Path(f"{self.model_path['local']}/{file_name}")
        bucket_path = f"{self.model_path['bucket']}"

        # Save the model locally
        torch.save(self.model.state_dict(), local_path)
        print(f"💾 Model saved locally at {local_path}")

        bucket = self.bucket.client.bucket("bestbrain")

        # Upload the model file to the bucket
        blob = bucket.blob(bucket_path)
        blob.upload_from_filename(local_path)
        print(f"🚀 Model uploaded to bucket at {bucket_path}")

    def load_model(self):
        """Load trained model"""
        if not os.path.exists(self.model_path["local"]):
            print("No local SAGE model found. Check bucket...")
            sage_models = []
            files = self.bucket.client.list_blobs(self.bucket.bucket_name, prefix=self.model_path["bucket"])
            for f in files:
                if f.startswith("sage".lower()):
                    sage_models.append(f.name)
            if len(sage_models) >= 1:
                model_with_most_layers = max(sage_models, key=len) if files else None
                self.bucket.client.download_blob_to_file(f"{self.model_path['local']}/{model_with_most_layers}")
            else:
                raise ValueError("⚠ No Model Found in Bucket. -> Run training first")
        try:
            files = [f for f in os.listdir(self.model_path["local"]) if f.startswith("sage".lower()) and f.endswith(".pth")]

            model_with_most_layers = max(files, key=len) if files else None

            self.model.load_state_dict(torch.load(model_with_most_layers, map_location=self.device))
            self.model.eval()
            print(f"✅ Model loaded from {self.model_path}")
        except Exception as e:
            print("Unable to load model:", e)

    def predict(self, node_id):
        """Predict embedding for a node"""
        with torch.no_grad():
            outputs = self.model(self.node_features, self.adjacency_matrices)
            return outputs[node_id].cpu().numpy()


class GraphSAGEModel(nn.Module):
    """GraphSAGE for scalable heterogeneous graph learning"""

    def __init__(self, in_dim, hidden_dim, out_dim, num_layers=2, sample_neighbors=10):
        super().__init__()
        self.sample_neighbors = sample_neighbors
        self.layers = nn.ModuleList()

        # Input layer
        self.layers.append(nn.Linear(in_dim, hidden_dim))

        # Hidden layers
        for _ in range(num_layers - 1):
            self.layers.append(nn.Linear(hidden_dim, hidden_dim))

        # Output layer
        self.out_layer = nn.Linear(hidden_dim, out_dim)

    def forward(self, node_features, adjacency_matrices):
        """GraphSAGE forward pass with improved layer-wise neighbor sampling"""
        out_features = node_features.clone()

        for layer in self.layers:
            new_features = torch.zeros_like(out_features)

            for rel, adj in adjacency_matrices.items():
                src, dst = adj.indices()

                # Sample based on layer depth
                sample_size = min(len(src), self.sample_neighbors)
                sampled_idx = torch.randperm(len(src))[:sample_size]
                src, dst = src[sampled_idx], dst[sampled_idx]

                # Improved aggregation
                new_features.index_add_(0, dst, out_features[src] / sample_size)

            out_features = layer(new_features)
            out_features = torch.relu(out_features)  # Non-linearity

        return self.out_layer(out_features)





class GraphSAGEVisualizer:
    """Class to visualize GraphSAGE model's structure and embeddings and upload to a Cloud Bucket."""

    def __init__(self, trainer: GraphSAGETrainer, bucket_name="bestbrain", save_path="visualizations"):
        """Initialize with a trained GraphSAGE model and graph, and configure cloud storage."""
        self.trainer = trainer  # Reference to the trainer
        self.G = trainer.G  # Original NetworkX graph
        self.model = trainer.model  # Trained GraphSAGE model
        self.node_features = trainer.node_features  # Node feature matrix
        self.adjacency_matrices = trainer.adjacency_matrices  # Adjacency data
        self.bucket_name = bucket_name
        self.save_path = save_path
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def save_and_upload(self, filename):
        """Uploads the generated image to the cloud bucket."""
        local_path = os.path.join(self.save_path, filename)
        plt.savefig(local_path)
        plt.close()

        blob = self.bucket.blob(f"{self.save_path}/{filename}")
        blob.upload_from_filename(local_path)
        print(f"✅ Uploaded {filename} to {self.bucket_name}/{self.save_path}")


    def visualize_graph(self):
        """Visualizes the original graph structure before training and uploads it."""
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.G)  # Compute layout
        nx.draw(self.G, pos, with_labels=True, node_size=300, node_color="skyblue", edge_color="gray")
        plt.title("Original Graph Structure")
        self.save_and_upload("original_graph.png")

    def visualize_sampled_graph(self, node_id, num_hops=2):
        """Visualizes the sampled GraphSAGE neighborhood around a specific node and uploads it."""
        sub_nodes = set()
        sub_nodes.add(node_id)

        for _ in range(num_hops):
            new_neighbors = set()
            for node in list(sub_nodes):
                new_neighbors.update(set(self.G.neighbors(node)))
            sub_nodes.update(new_neighbors)

        subgraph = self.G.subgraph(sub_nodes)
        pos = nx.spring_layout(subgraph)

        plt.figure(figsize=(10, 7))
        nx.draw(subgraph, pos, with_labels=True, node_color="lightblue", edge_color="gray", node_size=700)
        plt.title(f"Sampled GraphSAGE Neighborhood (Node {node_id})")
        self.save_and_upload(f"sampled_graph_{node_id}.png")

    def visualize_embeddings(self):
        """Projects and visualizes learned node embeddings using t-SNE and uploads it."""
        self.model.eval()
        with torch.no_grad():
            embeddings = self.model(self.node_features, self.adjacency_matrices).cpu().numpy()

        tsne = TSNE(n_components=2, perplexity=30, random_state=42)
        reduced_embeddings = tsne.fit_transform(embeddings)

        plt.figure(figsize=(10, 7))
        plt.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], s=50, c="blue", alpha=0.6)
        plt.title("GraphSAGE Node Embeddings - t-SNE Projection")
        self.save_and_upload("node_embeddings.png")
