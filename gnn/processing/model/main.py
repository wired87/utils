import json
import os

import aiofiles
from torch_geometric.nn import HeteroConv, Linear, SAGEConv
import torch


class HeteroGNN(torch.nn.Module):
    def __init__(self, metadata, hidden_channels, out_channels):
        super().__init__()
        # Define convolution layers for each edge type
        self.convs = HeteroConv({
            edge_type: SAGEConv((-1, -1), hidden_channels)
            for edge_type in metadata[1]
        })
        self.lin = Linear(hidden_channels, out_channels)

    def forward(self, x_dict, edge_index_dict):
        # Apply heterogeneous graph convolutions
        x_dict = self.convs(x_dict, edge_index_dict)
        # Apply activation
        x_dict = {key: x.relu() for key, x in x_dict.items()}
        # Apply linear transformation
        x_dict = {key: self.lin(x) for key, x in x_dict.items()}
        return x_dict

def validate_and_assign_labels(hetero_data, node_type, num_classes):
    """
    Validate if the node type has target labels. If missing, assign dummy labels.
    Args:
        hetero_data (HeteroData): The heterogeneous graph data structure.
        node_type (str): The node type to validate.
        num_classes (int): Number of classes for dummy label assignment.

    Returns:
        None: Updates the hetero_data in-place.
    """
    if not hasattr(hetero_data[node_type], 'y'):
        print(f"Warning: Node type '{node_type}' is missing target labels. Assigning dummy labels.")
        num_nodes = hetero_data[node_type].x.size(0)
        hetero_data[node_type].y = torch.randint(0, num_classes, (num_nodes,))
    else:
        print(f"Target labels for node type '{node_type}' are present.")



async def asave_data_checkpoint(path, content, mode="w", j=True):
    print("Save Data Checkpoint...")

    # Ensure the directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Write JSON content asynchronously
    if j:
        content= json.dumps(content, indent=2)
    async with aiofiles.open(path, mode=mode) as json_file:
        await json_file.write(content)

    print(f"Checkpoint saved successfully at {path}")

