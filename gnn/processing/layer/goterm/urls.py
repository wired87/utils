

def goterm_graph(go_id: str):
    return rf"https://api.geneontology.org/api/ontology/term/{go_id}/graph?graph_type=topology_graph"


def metadata(o_id):
    return rf"https://api.geneontology.org/api/ontology/term/{o_id}"

def gocams_for_goterm_url(go_id: str):
    return f"https://api.geneontology.org/api/go/{go_id}/models"



