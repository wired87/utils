import asyncio

from utils.ensembl import get_genes_from_go_ensembl
from rag.rag_handler import RagHandler


async def main(query):
    print("Starting")
    rh = RagHandler()
    go_ids = await rh.go_main(query, "eco")
    gene_data = await get_genes_from_go_ensembl(go_ids)


if __name__ == "__main__":
    asyncio.run(main("Dendrite development"))