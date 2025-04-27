import asyncio
from typing import List

import torch
import networkx as nx
import torch.nn.functional as F
import torch_geometric
from torch import nn, optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch_geometric.data import HeteroData, Data
from torch_geometric.nn import GATConv, SAGEConv, Linear, to_hetero
from torch_geometric.utils.convert import from_networkx
from torch.utils.data import DataLoader
import logging
from karateclub import Node2Vec

# Configure logging for production
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class GraphProcessor:
    """
    Handles graph embedding generation and conversion to PyTorch Geometric format.
    """

    def __init__(self, G, bucket=None):
        self.G = G
        self.bucket = bucket
        self.max_concurrent_tasks = 500
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self.model = Node2Vec(dimensions=128, walk_length=30, walk_number=200, workers=4)

    async def standardize_node_attributes(self, subgraph, default_value=0.0):
        """
        Ensure all nodes in a subgraph have the same set of attributes.
        This prevents conversion errors when creating PyG Data objects.

        Args:
            subgraph (networkx.Graph): A NetworkX subgraph containing only one node type.
            default_value (float, optional): Default value for missing attributes.
        """
        all_attributes = set()

        # Collect all unique attributes across nodes
        for _, data in subgraph.nodes(data=True):
            all_attributes.update(data.keys())

        # Fill missing attributes
        for _, data in subgraph.nodes(data=True):
            for attr in all_attributes:
                if attr not in data:
                    data[attr] = default_value  # Assign default value

    async def extract_subgraph(self, node_type):
        """
        Extract a subgraph containing only nodes of a specific type.

        Args:
            node_type (str): The node type to extract.

        Returns:
            networkx.Graph: A subgraph containing only nodes of the given type.
        """
        print(f"Extract subgraph for {node_type}")
        subgraph_nodes = [n for n, d in self.G.nodes(data=True) if d.get("layer") == node_type]
        subgraph = self.G.subgraph(subgraph_nodes).copy()

        # Standardize attributes to avoid PyG conversion errors
        await self.standardize_node_attributes(subgraph)
        return subgraph

    async def convert_to_hetero_data(self):
        print("Convert to HeteroData")
        """
        Convert a multi-layer NetworkX graph into a PyG HeteroData object.

        Returns:
            HeteroData: A PyTorch Geometric heterogeneous graph object.
        """
        hetero_data = HeteroData()

        # Get all unique node types
        node_types = set(d.get("layer") for _, d in self.G.nodes(data=True) if "layer" in d)  # Unique node types

        # Convert each node type separately
        for node_type in node_types:
            subgraph = await self.extract_subgraph(node_type)  # Get subgraph
            #pyg_data = from_networkx(subgraph)  # Convert to PyG Data object

            # Use the precomputed node embeddings if available
            embeddings = []
            for node in subgraph.nodes():
                embedding = self.G.nodes[node].get("embedding", torch.zeros(1024))  # Default to zero if missing
                embeddings.append(torch.tensor(embedding, dtype=torch.float))

            hetero_data[node_type].x = torch.stack(embeddings)  # Assign node embeddings

        # Convert edges, preserving relationships
        for src, dst, attrs in self.G.edges(data=True):
            edge_type = attrs.get("relationship", "default")
            src_type = self.G.nodes[src].get("layer")
            dst_type = self.G.nodes[dst].get("layer")
            src_embedding = torch.tensor([hash(src) % 1024], dtype=torch.float)
            dst_embedding = torch.tensor([hash(dst) % 1024], dtype=torch.float)

            if src_type and dst_type:
                # Store edge indices
                if (src_type, edge_type, dst_type) not in hetero_data:
                    hetero_data[(src_type, edge_type, dst_type)].edge_index = torch.tensor([],
                                                                                           dtype=torch.long).reshape(2,                                                                          0)
                    hetero_data[(src_type, edge_type, dst_type)].edge_attr = torch.tensor([], dtype=torch.float)
                # Append edge index
                edge_index_tensor = torch.tensor([[src_embedding], [dst_embedding]], dtype=torch.long)
                hetero_data[(src_type, edge_type, dst_type)].edge_index = torch.cat(
                    [hetero_data[(src_type, edge_type, dst_type)].edge_index, edge_index_tensor], dim=1
                )

                # Store precomputed edge embeddings if available
                edge_embedding = torch.tensor(self.G[src][dst].get("embedding", torch.zeros(1024), dtype=torch.float))  # Default to zero
                hetero_data[(src_type, edge_type, dst_type)].edge_attr = torch.cat(
                    [hetero_data[(src_type, edge_type, dst_type)].edge_attr, edge_embedding.unsqueeze(0)], dim=0
                )

        return hetero_data


import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.utils.data
import asyncio
import logging
from torch_geometric.nn import GATConv, SAGEConv, to_hetero
from torch_geometric.data import HeteroData
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, TensorDataset

class GNNTrainer:
    def __init__(self, pyg_data: HeteroData, bucket, hidden_dim=128, num_epochs=50, batch_size=1024, lr=1e-3, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.pyg_data = pyg_data.to(self.device)
        self.hidden_dim = hidden_dim
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        self.lr = lr
        self.bucket = bucket

        # Initialize model, optimizer, and scheduler
        self.model = self.build_model().to(self.device)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=5e-4)
        self.scheduler = ReduceLROnPlateau(self.optimizer, mode="min", factor=0.5, patience=5, verbose=True)
        self.criterion = nn.CrossEntropyLoss()

        # Create data loader
        self.train_loader = self.create_dataloader()

    def build_model(self):
        """
        Builds a GNN model.
        """

        class GNN(nn.Module):
            def __init__(self, metadata, hidden_dim):
                super().__init__()
                self.hidden_dim = hidden_dim

                self.conv1 = to_hetero(
                    GATConv((-1, -1), hidden_dim, heads=4, dropout=0.3),
                    metadata=metadata,
                    aggr="mean"
                )
                self.conv2 = to_hetero(
                    SAGEConv((-1, -1), hidden_dim, aggr="mean"),
                    metadata=metadata
                )
                self.batch_norm = nn.BatchNorm1d(hidden_dim)
                self.dropout = nn.Dropout(0.2)
                self.lin = nn.Linear(hidden_dim, 2)  # Binary classification

            def forward(self, x_dict, edge_index_dict):
                x_dict = self.conv1(x_dict, edge_index_dict)
                x_dict = {k: F.elu(v) for k, v in x_dict.items()}
                x_dict = self.conv2(x_dict, edge_index_dict)
                x_dict = {k: self.batch_norm(v) for k, v in x_dict.items()}
                x_dict = {k: self.dropout(v) for k, v in x_dict.items()}
                x_dict = {k: self.lin(v) for k, v in x_dict.items()}
                return x_dict

        return GNN(self.pyg_data.metadata(), self.hidden_dim)

    def create_dataloader(self):
        """
        Creates a data loader for training in batches.
        """
        node_features = self.pyg_data["protein"].x  # Ensure correct node type is used
        labels = self.pyg_data["protein"].y if "y" in self.pyg_data["protein"] else torch.zeros(node_features.size(0))

        dataset = TensorDataset(node_features, labels)
        return DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

    def train(self):
        """
        Trains the GNN model with logging and validation.
        """
        logging.info(f"🚀 Starting training on {self.device}")

        for epoch in range(1, self.num_epochs + 1):
            self.model.train()
            total_loss = 0

            for node_features, labels in self.train_loader:
                node_features, labels = node_features.to(self.device), labels.to(self.device)

                self.optimizer.zero_grad()
                out_dict = self.model(self.pyg_data.x_dict, self.pyg_data.edge_index_dict)

                # Compute loss
                out = out_dict["protein"]  # Ensure correct node type is used
                loss = self.criterion(out, labels.long())  # Convert to LongTensor for classification

                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(self.train_loader)
            self.scheduler.step(avg_loss)

            logging.info(f"Epoch {epoch}/{self.num_epochs}, Loss: {avg_loss:.4f}")

    def evaluate(self):
        """
        Evaluates the trained model.
        """
        self.model.eval()
        correct, total = 0, 0

        with torch.no_grad():
            out_dict = self.model(self.pyg_data.x_dict, self.pyg_data.edge_index_dict)
            out = out_dict["protein"]  # Ensure correct node type is used
            preds = torch.argmax(out, dim=1)
            labels = self.pyg_data["protein"].y.to(self.device)

            correct += (preds == labels).sum().item()
            total += labels.size(0)

        accuracy = correct / total
        logging.info(f"✅ Model Accuracy: {accuracy:.4f}")
        return accuracy

    def save_model(self, bucket_path, local_path):
        """
        Saves the trained model.
        """
        torch.save(self.model, local_path)  # Save the entire model, not just state_dict
        logging.info(f"💾 Model saved locally at {local_path}")
        asyncio.run(self.bucket.upload_json_to_folder(bucket_path=bucket_path, local_path=local_path))
        logging.info(f"💾 Model saved in bucket {bucket_path}")

    def load_model(self, model_path):
        """
        Loads the trained model from file.
        """
        self.model = torch.load(model_path, map_location=self.device)
        self.model.to(self.device)
        logging.info(f"📤 Model loaded from {model_path}")






