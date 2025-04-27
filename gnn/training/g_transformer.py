import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import TransformerConv

# 🔹 Optional: Cloud Storage (Google Cloud Storage / AWS S3)
from google.cloud import storage  # Google Cloud



class GraphTransformerModel:
    def __init__(self, g_utils, in_channels=16, hidden_channels=32, out_channels=2, num_heads=2, cloud_provider="gcp"):
        """
        Initializes the Graph Transformer model.
        :param in_channels: Input feature dimensions per node.
        :param hidden_channels: Hidden layer dimensions.
        :param out_channels: Output feature dimensions.
        :param num_heads: Number of attention heads in Transformer layers.
        :param cloud_provider: Choose "gcp" for Google Cloud Storage or "aws" for S3.
        """
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self.build_model(in_channels, hidden_channels, out_channels, num_heads).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01, weight_decay=5e-4)
        self.cloud_provider = cloud_provider
        self.g_utils = g_utils

    def build_model(self, in_channels, hidden_channels, out_channels, num_heads):
        """Defines the Transformer-based Graph Neural Network model."""

        class GraphTransformer(torch.nn.Module):
            def __init__(self):
                super(GraphTransformer, self).__init__()
                self.conv1 = TransformerConv(in_channels, hidden_channels, heads=num_heads, dropout=0.1)
                self.conv2 = TransformerConv(hidden_channels * num_heads, out_channels, heads=1, dropout=0.1)

            def forward(self, data):
                x, edge_index = data.x, data.edge_index
                x = self.conv1(x, edge_index).relu()
                x = self.conv2(x, edge_index)
                return x

        return GraphTransformer()

    def convert_networkx_to_pyg(self, G):
        """Converts a NetworkX graph to PyTorch Geometric Data format."""
        node_features = torch.randn(len(G.nodes), 16)  # Random 16-dim features
        edge_index = torch.tensor(list(G.edges)).t().contiguous()
        return Data(x=node_features, edge_index=edge_index).to(self.device)

    def train(self, data, epochs=100):
        """Trains the Graph Transformer model."""
        data = data.to(self.device)
        for epoch in range(epochs):
            self.model.train()
            self.optimizer.zero_grad()
            out = self.model(data)
            loss = F.mse_loss(out, torch.rand_like(out))  # Dummy loss for example
            loss.backward()
            self.optimizer.step()

            if epoch % 10 == 0:
                print(f"Epoch {epoch} | Loss: {loss.item():.4f}")

        print("✅ Training Completed!")

    def save_model(self, save_path):
        """Saves the trained model locally."""
        torch.save(self.model.state_dict(), save_path)
        print(f"✅ Model saved locally at {save_path}")


    def upload_to_gcp(self, bucket_name, destination_path, src):
        """Uploads the model to Google Cloud Storage."""
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(destination_path)
        blob.upload_from_filename(src)
        print(f"✅ Model uploaded to GCP: gs://{bucket_name}/{destination_path}")





    def main(self, local_save_path=r"C:\Users\wired\OneDrive\Desktop\Projects\pythonProject\main_ckpt\model\go_term.pth"):
        # Initialize the Graph Transformer model

        # Convert the graph to PyTorch Geometric format
        pyg_data = self.convert_networkx_to_pyg(self.g_utils.G)

        # Train the model
        self.train(pyg_data, epochs=100)

        # Save the trained model locally
        self.save_model(local_save_path)

        # Upload to Cloud (GCP or AWS)
        BUCKET_NAME = "bestbrain"  # Replace with your GCP or AWS bucket
        DEST_PATH = "graph_embed/goterm_transformer.pth"
        self.upload_to_gcp(BUCKET_NAME, DEST_PATH, src=local_save_path)





