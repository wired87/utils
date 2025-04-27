


import os
import json
import asyncio

import numpy as np
import torch
import torch.nn.functional as F
import networkx as nx
from torch_geometric.data import HeteroData
from torch_geometric.nn import TransformerConv
from transformers import AutoTokenizer, AutoModel

from utils.ggoogle.storage.storage import GBucket
from utils.gnn import NX_LOCAL_CKPT, NX_BUCKET_CKPT, SRC_PATH
from utils.gnn.embedder import embed
from utils.gnn.processing.model.main import asave_data_checkpoint

r"""

Traceback (most recent call last):
  File "C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\gnn\main.py", line 229, in <module>
    asyncio.run(gtm.main())
  File "C:\Users\wired\AppData\Local\Programs\Python\Python39\lib\asyncio\runners.py", line 44, in run
    return loop.run_until_complete(main)
  File "C:\Users\wired\AppData\Local\Programs\Python\Python39\lib\asyncio\base_events.py", line 647, in run_until_complete
    return future.result()
  File "C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\gnn\hetero\main.py", line 85, in main
    await self.load_and_convert_graphs()
  File "C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\gnn\hetero\main.py", line 140, in load_and_convert_graphs
    await self.process_edges(G)
  File "C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\gnn\hetero\main.py", line 274, in process_edges
    await asyncio.gather(*tasks)
  File "C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\gnn\hetero\main.py", line 295, in process_edge
    src_id = self.node_id_mapping.get(G.nodes[src], 0.0)
TypeError: unhashable type: 'dict'

Process finished with exit code 1
"""

# todo save dicts
class HeteroGraphConvGTTrainer:
    def __init__(self, bucket_name, info=None, graph_of_interest=None, embedding_dim=16):
        """
        Initializes the heterogeneous graph trainer.
        :param bucket_name: GCS bucket name for storage
        :param info: Metadata and paths
        :param graph_of_interest: The specific graph to train on
        :param embedding_dim: Node feature dimension
        """
        print("🔹 Initializing Graph Trainer...")

        self.graph_dir = NX_LOCAL_CKPT
        self.bucket_dir = NX_BUCKET_CKPT
        self.bucket = GBucket(bucket_name)
        self.general_stuff = info or SRC_PATH
        self.embedding_dim = embedding_dim
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.graph_of_interest = graph_of_interest
        self.hetero_data = HeteroData()
        self.nxG = nx.Graph()

        self.node_id_mapping = {}  # Maps all possible node attributes
        self.node_feature_mapping = {}  # Node attribute storage
        self.edge_feature_mapping = {}  # Edge attribute storage

        self.batch_size = 1000
        print(f"🔹 Using device: {self.device}")

        # Load Pretrained Text Embedding Model
        try:
            print("🔹 Loading BERT Tokenizer & Model...")
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            self.model = AutoModel.from_pretrained("bert-base-uncased").to(self.device)
        except Exception as e:
            print(f"❌ Error loading BERT model: {e}")
            exit(1)

        self.lock = asyncio.Lock()
        print("✅ Graph Trainer Initialized Successfully.")


    def get_args_save_path(self):
        return {
            "node_id_mapping": self.node_id_mapping,
            "node_feature_mapping": self.node_feature_mapping,
            "edge_feature_mapping": self.edge_feature_mapping
        }

    async def save_model_local(self, bas_path, model):
        model_path = os.path.join(bas_path, self.graph_of_interest + ".pth")
        torch.save(model.state_dict(), model_path)
        await asyncio.gather(*[asave_data_checkpoint(path=os.path.join(bas_path, f"{k}.json"), content=v) for k,v in self.get_args_save_path().items()])
        print(f"✅ Model content saved at: {model_path}")


    async def main(self):
        """
        1️⃣ Downloads & Loads Graphs
        2️⃣ Converts to HeteroData
        3️⃣ Trains a Graph Transformer
        4️⃣ Saves & Uploads Model
        """
        print("🚀 Starting the Graph Processing Pipeline...")
        await self.load_and_convert_graphs()

        await self.process_model()


    async def process_model(self):
        model = await self.train_graph_transformer()

        # ✅ Save trained model
        print("💾 Saving Model Locally...")
        model_dir_local = os.path.join(self.general_stuff["paths"]["model"]["local"], self.graph_of_interest + "/")
        model_dir_bucket = os.path.join(self.general_stuff["paths"]["model"]["bucket"], self.graph_of_interest + "/")
        model_file = os.path.join(model_dir_local, f"{self.graph_of_interest}.pth")
        await self.save_model_local(model_dir_local, model)

        print("📤 Uploading Model to Cloud Storage...")
        await asyncio.gather(*[self.bucket.upload_file(
            remote_path=os.path.join(model_dir_bucket, f"{k}.json"),
            local_file_path=os.path.join(model_dir_local, f"{k}.json"),
        ) for k, v in self.get_args_save_path().items()])

        # ✅ Evaluate Model
        print("🧪 Evaluating Model...")
        await self.test_model(model, model_file)





    async def load_and_convert_graphs(self):
        """Loads multiple NetworkX graphs and converts them into a HeteroData object."""
        print("🔄 Checking for Graph Files...")
        if not os.path.exists(self.graph_dir) or len(os.listdir(self.graph_dir)) == 0:
            print("📥 No local graphs found, downloading from cloud...")
            await self.bucket.download_folder_content_or_single(
                prefix=self.bucket_dir,
                name=f"{self.graph_of_interest}.json"
            )

        files = [f for f in os.listdir(self.graph_dir) if f.endswith(".json")]
        file_names_str = "_".join([os.path.splitext(f)[0] for f in files])
        self.graph_of_interest = file_names_str
        print("Save file name set to ", self.graph_of_interest)
        if not files:
            print("❌ No graph files found! Exiting...")
            exit(1)

        print(f"📂 Found {len(files)} graph files.")

        for file in files:
            graph_path = os.path.join(self.graph_dir, file)
            print(f"🔹 Loading Graph: {graph_path}")

            try:
                with open(graph_path, "r", encoding="utf-8") as f:
                    graph_data = json.load(f)
                G = nx.node_link_graph(graph_data)
            except Exception as e:
                print(f"❌ Error loading graph {file}: {e}")
                continue

            # Process nodes and edges
            await self.process_nodes(G)
            await self.process_edges(G)

        # ✅ Convert lists to tensors
        print("🔄 Converting Graph Features to Tensors...")
        await self.convert_features()
        await self.convert_edges()
        print("✅ Graphs Successfully Converted to HeteroData.")


    async def convert_edges(self):
        """Converts edge index and weight lists into tensors."""
        print("Handle edges")
        for edge_type in self.hetero_data.edge_types:
            self.hetero_data[edge_type].edge_index = torch.tensor(
                self.hetero_data[edge_type].edge_index, dtype=torch.long
            )
            self.hetero_data[edge_type].edge_weight = torch.stack(self.hetero_data[edge_type].edge_weight)
            self.hetero_data[edge_type].edge_attrs = torch.stack(self.hetero_data[edge_type].edge_attrs)




    async def test_model(self, model, model_path):

        # Load the trained model
        model.load_state_dict(torch.load(model_path))
        model.to(self.device)
        model.eval()

        # Move test data to device
        test_data = self.hetero_data.to(self.device)

        # Forward pass
        with torch.no_grad():
            predictions = model(test_data)

        # Define a test label tensor (replace with actual test labels if available)
        # Ideally, you should have a separate y_test tensor from a validation set
        true_labels = torch.rand_like(predictions).to(self.device)  # Placeholder, replace with real labels

        # Compute Mean Squared Error (for regression tasks)
        mse_loss = F.mse_loss(predictions, true_labels)
        print(f"📉 Test MSE Loss: {mse_loss.item():.4f}")

        # If this is a classification task:
        if predictions.shape[-1] > 1:  # If multi-class, apply softmax
            pred_classes = predictions.argmax(dim=-1)
            true_classes = true_labels.argmax(dim=-1)  # Assuming one-hot encoding for true labels
        else:  # For binary classification
            pred_classes = (predictions > 0.5).long()
            true_classes = (true_labels > 0.5).long()

        # Compute Accuracy
        accuracy = (pred_classes == true_classes).float().mean().item()
        print(f"✅ Model Accuracy: {accuracy:.4%}")

        # Optional: Print example predictions
        print("🔍 Sample Predictions vs. True Labels:")
        for i in range(min(5, len(pred_classes))):
            print(f"Pred: {pred_classes[i].item()}, True: {true_classes[i].item()}")

    async def get_embedding(self, text):
        """Asynchronously convert text to embeddings using BERT."""
        embeddings =embed(text)
        return embeddings

    async def embed_process(self, k, v, feature_dict):
        if k not in feature_dict:
            feature_dict.setdefault(k, len(feature_dict))

        if isinstance(v, str):
            feature = await self.get_embedding(v)
        elif isinstance(v, (int, float)):
            feature = torch.tensor([v], dtype=torch.float)
        elif isinstance(v, bool):
            feature = torch.tensor([1.0]) if v else torch.tensor([0.0])
        else:
            feature = torch.zeros(self.embedding_dim)  # Default zero

        return feature


    async def process_nodes(self, G):
        """Processes nodes and assigns features in batches to optimize performance."""
        print(f"📍 Processing {len(G.nodes)} Nodes...")

        nodes = list(G.nodes(data=True))  # Convert to list to support batching

        for i in range(0, len(nodes), self.batch_size):
            batch = nodes[i:i + self.batch_size]  # Get next batch of 100 nodes
            tasks = [self.process_node(node, attrs) for node, attrs in batch]
            await asyncio.gather(*tasks)  # Process batch asynchronously
            print(f"✅ Processed batch {i // self.batch_size + 1}/{(len(nodes) + self.batch_size - 1) // self.batch_size}")

    async def process_node(self, node_id, attrs):
        """Handles feature embedding for nodes."""

        if attrs is None:
            raise ValueError(f"Node {node_id} has no attributes!")

        node_type = attrs.get("layer") or attrs.get("type") or "default"  # Ensure node_type is valid

        self.node_id_mapping[str(node_id)] = len(self.node_id_mapping) + 1  # Unique IDs
        node_features = await asyncio.gather(
            *[self.embed_process(k, v, self.node_feature_mapping) for k, v in attrs.items()]
        )

        if len(node_features) > 0:
            node_features = [torch.tensor(f, dtype=torch.float) if isinstance(f, np.ndarray) else f for f in
                             node_features]

            cat_n_features = torch.cat(node_features, dim=0)
            #print("cat_n_features", cat_n_features)
            node_features = cat_n_features
        else:
            node_features = torch.zeros(self.embedding_dim)  # Default zero vector
        async with self.lock:
            if node_type not in self.hetero_data:
                self.hetero_data[node_type].x = node_features.unsqueeze(0)
                self.hetero_data[node_type].node_id = torch.tensor([self.node_id_mapping[str(node_id)]],
                                                                   dtype=torch.long)
            else:
                self.hetero_data[node_type].x = torch.cat(
                    [self.hetero_data[node_type].x, node_features.unsqueeze(0)], dim=0
                )
                self.hetero_data[node_type].node_id = torch.cat(
                    [self.hetero_data[node_type].node_id,
                     torch.tensor([self.node_id_mapping[str(node_id)]], dtype=torch.long)], dim=0
                )

    async def process_edges(self, G):
        """Processes edges and assigns relationships."""
        print(f"📍 Processing {len(G.edges)} Nodes...")
        tasks = [self.process_edge(src, dst, attrs, G) for src, dst, attrs in G.edges(data=True)]
        await asyncio.gather(*tasks)


    async def process_edge(self, src, dst, attrs, G):
        """Processes edges and assigns embeddings."""

        # Get edge relationship type embedding (default to "default" if missing)
        rel = attrs.get("relationship", "default")
        str_src_layer = G.nodes[src].get("layer", "default")
        str_dst_layer = G.nodes[dst].get("layer", "default")
        print("embed edge_type:", str_src_layer, "->", rel, "->", str_dst_layer)

        edge_type = (str_src_layer, rel, str_dst_layer)

        # Ensure node types are mapped if they exist in node_id_mapping
        src_id = self.node_id_mapping.get(G.nodes[src], 0.0)
        dst_id = self.node_id_mapping.get(G.nodes[dst], 0.0)

        edge_features = await asyncio.gather(
            *[self.embed_process(k, v, self.edge_feature_mapping) for k, v in attrs.items()]
        )

        edge_weight = torch.tensor([float(attrs.get("weight", 1.0))], dtype=torch.float)

        async with self.lock:
            if edge_type not in self.hetero_data:
                self.hetero_data[edge_type].edge_index = ([], [])
                self.hetero_data[edge_type].edge_weight = []
                self.hetero_data[edge_type].edge_attrs = []

            self.hetero_data[edge_type].edge_index[0].append(src_id)
            self.hetero_data[edge_type].edge_index[1].append(dst_id)

            self.hetero_data[edge_type].edge_weight.append(edge_weight)
            self.hetero_data[edge_type].edge_attrs.append(edge_features)

    async def train_graph_transformer(self, epochs=30, lr=0.01):
        """Trains a Graph Transformer model on HeteroData."""
        print("🚀 Starting Graph Transformer Training...")

        class GraphTransformer(torch.nn.Module):
            def __init__(self, in_channels, hidden_channels, out_channels, num_heads):
                super(GraphTransformer, self).__init__()
                self.conv1 = TransformerConv(in_channels, hidden_channels, heads=num_heads, dropout=0.1)
                self.conv2 = TransformerConv(hidden_channels * num_heads, out_channels, heads=1, dropout=0.1)

            def forward(self, data):
                x, edge_index = data.x, data.edge_index
                x = self.conv1(x, edge_index).relu()
                x = self.conv2(x, edge_index)
                return x

        model = GraphTransformer(in_channels=self.embedding_dim, hidden_channels=32, out_channels=2, num_heads=2)
        model.to(self.device)
        optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)

        self.hetero_data.to(self.device)

        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            out = model(self.hetero_data)
            loss = F.mse_loss(out, torch.rand_like(out))
            loss.backward()
            optimizer.step()

            if epoch % 10 == 0:
                print(f"🟢 Epoch {epoch} | Loss: {loss.item():.4f}")

        print("✅ Training Completed!")
        return model

    async def convert_features(self):
        """Converts node feature lists into tensors and ensures correct formatting."""
        for node_type in self.hetero_data.node_types:
            if isinstance(self.hetero_data[node_type].x, list):
                try:
                    # Convert list of tensors to a single stacked tensor
                    self.hetero_data[node_type].x = torch.stack(self.hetero_data[node_type].x)
                except RuntimeError:
                    # Handle shape mismatch by padding or converting to uniform dimensions
                    self.hetero_data[node_type].x = torch.cat(
                        [x.unsqueeze(0) if x.dim() == 1 else x for x in self.hetero_data[node_type].x], dim=0)

            # Ensure node_id remains intact and safe from accidental modification
            self.hetero_data[node_type].node_id = self.hetero_data[node_type].node_id.clone() if isinstance(
                self.hetero_data[node_type].node_id, torch.Tensor) else self.hetero_data[node_type].node_id



