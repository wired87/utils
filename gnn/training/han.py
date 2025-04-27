"""
Do not use dgl anymore but keep functionality fr the hetero graph
attention network. Do not manipulate any of the gien graph attribuees,

their ids or anything else in any kind. You know how to train a hetero
graph atention network so use bet practices to train one of them from
the provided nx.Graph. AVOID unessessary lines of code. Less is more!
"""
import asyncio
import os
import torch
import torch.nn as nn
import torch.optim as optim
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
import random

from ggoogle.storage.storage import GBucket


class HANModel(nn.Module):
    """ Heterogeneous Graph Attention Network (HAN) """

    def __init__(self, in_dim, hidden_dim, out_dim, num_heads, relations):
        super().__init__()

        # Dynamically initialize layers based on relations in the graph
        self.layers = nn.ModuleDict({
            f"rel_{rel}": nn.MultiheadAttention(embed_dim=in_dim, num_heads=num_heads)
            for rel in relations
        })

        self.fc = nn.Linear(in_dim, out_dim)

    def forward(self, node_features, adjacency_matrices):
        batch_size = 1000  # Reduce depending on memory availability
        num_nodes = node_features.shape[0]

        out = {}

        for start in range(0, num_nodes, batch_size):
            end = min(start + batch_size, num_nodes)
            batch_features = node_features[start:end]

            for relation, attn_layer in self.layers.items():
                clean_relation = relation.replace("rel_", "")
                if clean_relation in adjacency_matrices:
                    attn_out, _ = attn_layer(batch_features, batch_features, batch_features)
                    if clean_relation not in out:
                        out[clean_relation] = []
                    out[clean_relation].append(self.fc(attn_out))

        # Combine batches
        for key in out:
            out[key] = torch.cat(out[key], dim=0)

        return out


class HANTrainer:
    """ Trains and manages the HAN model """

    def __init__(self, G: nx.Graph, info, layer, embedding_dim=128, hidden_dim=64, num_heads=4, epochs=10):
        self.G = G
        self.embedding_dim = embedding_dim
        self.epochs = epochs
        self.info = info
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.layer = layer
        self.node_features, self.adjacency_matrices = self._process_graph(G)

        # ✅ Pass actual relations into HANModel
        self.model = HANModel(embedding_dim, hidden_dim, embedding_dim, num_heads, relations=self.adjacency_matrices.keys()).to(self.device)

        self.bucket = GBucket("bestbrain")



    def _process_graph(self, G, sample_neighbors=10):
        node_mapping = {node: idx for idx, node in enumerate(G.nodes())}
        num_nodes = len(G)

        node_features = torch.randn(num_nodes, self.embedding_dim, device=self.device)
        node_features = nn.functional.normalize(node_features, dim=1)

        from collections import defaultdict
        adjacency_matrices = defaultdict(lambda: ([], []))

        for u, v, data in G.edges(data=True):
            rel = str(data.get("relationship", "interacts") or "interacts")

            if u in node_mapping and v in node_mapping:
                adjacency_matrices[rel][0].append(node_mapping[u])
                adjacency_matrices[rel][1].append(node_mapping[v])

        # **Randomly sample neighbors** to prevent too much computation
        for rel in adjacency_matrices:
            src, dst = adjacency_matrices[rel]
            if len(src) > sample_neighbors:
                sampled_idx = random.sample(range(len(src)), sample_neighbors)
                adjacency_matrices[rel] = ([src[i] for i in sampled_idx], [dst[i] for i in sampled_idx])

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
        """ Train HAN model """
        if not self.adjacency_matrices:
            raise ValueError("⚠ No valid adjacency matrices found! The graph may be empty or incorrectly processed.")

        self.model.train()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        loss_fn = nn.MSELoss()

        print("🚀 Training HAN model...")

        for epoch in range(self.epochs):
            optimizer.zero_grad()
            outputs = self.model(self.node_features, self.adjacency_matrices)

            # 🔹 Check if output are valid
            if not outputs:
                print(f"Epoch {epoch + 1}: No valid outputs from HANModel!")
                continue

            losses = []
            for rel in outputs:
                if outputs[rel].shape != self.node_features.shape:
                    print(f"⚠ Mismatch in shapes: {outputs[rel].shape} vs {self.node_features.shape}")
                    continue
                losses.append(loss_fn(outputs[rel], self.node_features))

            if not losses:
                print(f"Epoch {epoch + 1}: No valid losses computed.")
                continue

            loss = torch.stack(losses).mean()
            loss.backward()

            optimizer.step()
            print(f"Epoch {epoch + 1}/{self.epochs}, Loss: {loss.item():.4f}")

        self.save_model()

    def save_model(self):
        """ Save trained HAN model """
        local_path = self.info['paths']['graph_embed']["local"]
        bucket_path = self.info['paths']['graph_embed']["bucket"]

        # ✅ Fix invalid file path issue
        os.makedirs(local_path, exist_ok=True)
        model_path = os.path.join(local_path, "han_model.pth")
        torch.save(self.model.state_dict(), model_path)

        print(f"💾 Model saved at {model_path}")

        # ✅ Fix file naming issue for async upload
        file_name = "_".join(self.layer) + ".pth"
        asyncio.run(self.bucket.upload_bucket(
            dest_path=os.path.join(bucket_path, file_name),
            src_path=model_path,
        ))

    def load_model(self):
        """ Load HAN model """
        local_path = self.info['paths']['graph_embed']["local"]
        model_path = os.path.join(local_path, "han_model.pth")

        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            print(f"✅ Model loaded from {model_path}")
        else:
            print("⚠ No model found. Train the model first.")

    def predict(self, node_id):
        """ Predict embedding for a node """
        with torch.no_grad():
            outputs = self.model(self.node_features, self.adjacency_matrices)
            return outputs['interacts'][node_id].cpu().numpy()

    def find_similar_nodes(self, node_id, top_k=5):
        """ Find similar nodes based on cosine similarity """
        node_embedding = self.predict(node_id)
        all_embeddings = self.node_features.cpu().numpy()
        similarities = cosine_similarity([node_embedding], all_embeddings)[0]
        return sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)[1:top_k+1]


def han_main(graph_model):
    trainer = HANTrainer(graph_model.G, epochs=30, layer=graph_model.success_list,
                         info=graph_model.general_stuff)  # Initialize with networkx graph
    trainer.train()  # Train HAN model
    trainer.load_model()  # Load trained model

    # 🔹 Predict embedding for node 0
    node_embedding = trainer.predict(node_id=0)
    print("🔹 Predicted Node Embedding:", node_embedding)

    # 🔹 Find similar nodes
    similar_nodes = trainer.find_similar_nodes(node_id=0, top_k=3)
    print("🔍 Most similar nodes:", similar_nodes)