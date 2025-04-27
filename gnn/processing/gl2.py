import networkx as nx
import torch

from gnn.bridge.main import model


# Node Processing with ML
def process_node_data(node_id, G, input_data):
    if not G.has_node(node_id):
        print(f"Node {node_id} does not exist.")
        return None

    node = G.nodes[node_id]
    model = node.get("ml_model")  # Each node has its own ML model
    if not model:
        print(f"No ML model associated with node {node_id}.")
        return None

    # Simulate processing input data
    input_tensor = torch.tensor(input_data, dtype=torch.float32).unsqueeze(0)  # Add batch dimension
    result = model(input_tensor).detach().numpy()
    print(f"Node {node_id} processed data. Result: {result}")
    return result


# Handle Gene Edges and Create ML Models
def handle_gene_edges_with_ml(gene, G):
    gene_id = gene.get("id")

    # Add the gene as a node
    G.add_node(
        gene_id,
        **gene,
    )

    # Connect to related nodes
    for key, value in gene.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):  # List of IDs (e.g., xrefs)
                    G.add_edge(gene_id, item, type=key)
                elif isinstance(item, dict):  # Nested attributes
                    chat = model.start_chat()

                    identifier = get_gem(
                            prompt=f"""
                            Analyze the given object, return its identifier.
                            Content {gene} 
                            """"",
                            chat=chat
                        )
                    if identifier:
                        G.add_edge(gene_id, identifier, type=key, relationship="hi")


# Process Gene Layer
async def process_gene_layer_with_ml(data):
    G = nx.Graph()

    # Add genes and their relationships
    for gene in data['genes']:
        handle_gene_edges_with_ml(gene, G)

    return G



def get_gem(prompt, chat):
    response = chat.send_message(prompt)
    print("response", response)
    return response.candidates[0].content.parts[0]


