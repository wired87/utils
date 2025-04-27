def integrate_cross_layer(data, hetero_data):
    for edge in data['gene_cell_edges']:
        hetero_data["gene", "expressed_in", "cell"].edge_index.append(
            [edge['gene_id'], edge['cell_id']]
        )
    for edge in data['gene_protein_edges']:
        hetero_data["gene", "encodes", "protein"].edge_index.append(
            [edge['gene_id'], edge['protein_id']]
        )
    for edge in data['cell_protein_edges']:
        hetero_data["cell", "produces", "protein"].edge_index.append(
            [edge['cell_id'], edge['protein_id']]
        )
    return hetero_data