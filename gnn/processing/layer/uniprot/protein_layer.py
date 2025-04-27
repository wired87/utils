

class ProteinLayer:
    async def main(self, data, G):
        for edge in data['protein_edges']:
            G.add_edge(edge['source'], edge['target'], weight=edge['weight'], type=edge['type'])

        for protein in data['results']:
            G.add_node(
                protein['primaryAccession'],
                **protein,
                layer='protein'
            )


