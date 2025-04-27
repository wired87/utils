ENS_BASE_URL = "https://rest.ensembl.org"
ENS_HEADERS = {"Content-Type": "application/json"}

def gene_info_url(gene_name):
    return ENS_BASE_URL+f"/lookup/symbol/homo_sapiens/{gene_name}?expand=1"


def gene_sequence_url(gene_name):
    return ENS_BASE_URL+f"/sequence/region/human/GRCh38/{gene_name}:1-1000000"