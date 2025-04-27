import torch
import torch.nn as nn
from torch_geometric.data import HeteroData
import networkx as nx


class GraphConverter:
    def __init__(self, nx_graph):
        self.G = nx_graph
        self.hetero_data = HeteroData()
        self.node_embedding_layers = {}  # Store embeddings for categorical node attributes
        self.edge_embedding_layers = {}  # Store embeddings for categorical edge attributes

    async def to_heterogeneous_graph(self):
        print("🚀 Converting NetworkX Graph to HeteroData...")

        # STEP 1: CREATE NODE MAPPINGS (Assigning IDs)
        node_mapping = {}
        for i, (node, attributes) in enumerate(self.G.nodes(data=True)):
            layer = attributes.get("layer")  # Default node type if missing
            if layer not in self.hetero_data:
                self.hetero_data[layer].x = torch.empty((0, len(attributes)), dtype=torch.float)

            node_mapping[node] = (layer, len(self.hetero_data[layer].x))  # Store layer and index

        print("✅ Node mappings created.")

        # STEP 2: CONVERT NODE FEATURES
        node_features = {layer: [] for layer in self.hetero_data.node_types}
        for node, attributes in self.G.nodes(data=True):
            layer, idx = node_mapping[node]

            # Convert categorical attributes into embeddings
            processed_features = []
            for key, value in attributes.items():
                if isinstance(value, str):  # Categorical feature (e.g., 'protein_coding')
                    if key not in self.node_embedding_layers:
                        unique_values = list(set(nx.get_node_attributes(self.G, key).values()))
                        self.node_embedding_layers[key] = nn.Embedding(len(unique_values), 4)
                    value_idx = torch.tensor([unique_values.index(value)], dtype=torch.long)
                    embedded_value = self.node_embedding_layers[key](value_idx).squeeze(0)
                    processed_features.append(embedded_value)
                elif isinstance(value, (int, float)):  # Numeric feature
                    processed_features.append(torch.tensor([value], dtype=torch.float))

            if processed_features:
                node_features[layer].append(torch.cat(processed_features, dim=0))

        # Convert to tensors
        for layer, features in node_features.items():
            if features:
                self.hetero_data[layer].x = torch.stack(features)
            else:
                self.hetero_data[layer].x = torch.empty((0, 4), dtype=torch.float)  # Default 4D empty tensor

        print("✅ Node features converted.")

        # STEP 3: CONVERT EDGES
        edge_features = {edge_type: [] for edge_type in self.hetero_data.edge_types}
        edge_indices = {edge_type: [[], []] for edge_type in self.hetero_data.edge_types}

        for src, dst, attributes in self.G.edges(data=True):
            src_layer, src_idx = node_mapping[src]
            dst_layer, dst_idx = node_mapping[dst]
            edge_type = attributes.get("relationship", "default")  # Default edge type

            if (src_layer, edge_type, dst_layer) not in self.hetero_data.edge_types:
                self.hetero_data[(src_layer, edge_type, dst_layer)].edge_index = torch.empty((2, 0), dtype=torch.long)

            # Append edge indices
            edge_indices[(src_layer, edge_type, dst_layer)][0].append(src_idx)
            edge_indices[(src_layer, edge_type, dst_layer)][1].append(dst_idx)

            # Convert edge attributes
            processed_edge_features = []
            for key, value in attributes.items():
                if isinstance(value, str):  # Categorical edge attribute
                    if key not in self.edge_embedding_layers:
                        unique_values = list(set(nx.get_edge_attributes(self.G, key).values()))
                        self.edge_embedding_layers[key] = nn.Embedding(len(unique_values), 4)
                    value_idx = torch.tensor([unique_values.index(value)], dtype=torch.long)
                    embedded_value = self.edge_embedding_layers[key](value_idx).squeeze(0)
                    processed_edge_features.append(embedded_value)
                elif isinstance(value, (int, float)):  # Numeric attribute
                    processed_edge_features.append(torch.tensor([value], dtype=torch.float))

            if processed_edge_features:
                edge_features[(src_layer, edge_type, dst_layer)].append(torch.cat(processed_edge_features, dim=0))

        # Convert edge lists and attributes to tensors
        for edge_type in edge_indices:
            self.hetero_data[edge_type].edge_index = torch.tensor(edge_indices[edge_type], dtype=torch.long)
            if edge_features[edge_type]:
                self.hetero_data[edge_type].edge_attr = torch.stack(edge_features[edge_type])
            else:
                self.hetero_data[edge_type].edge_attr = torch.empty((0, 4), dtype=torch.float)

        print("✅ Edge features and indices converted.")
        print("🚀 Heterogeneous Graph Ready for Training!")

        return self.hetero_data
