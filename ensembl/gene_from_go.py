import aiohttp
import asyncio

from utils.ensembl import ENS_BASE_URL, ENS_HEADERS


async def fetch_json(session, url):
    """Helper function to fetch JSON data asynchronously."""
    async with session.get(url, headers=ENS_HEADERS) as response:
        if response.status == 200:
            return await response.json()
        return None

async def fetch_gene_info(session, gene_id):
    """Fetches detailed gene information including metadata and sequence."""
    gene_url = f"{ENS_BASE_URL}/lookup/id/{gene_id}?expand=1"
    seq_url = f"{ENS_BASE_URL}/sequence/id/{gene_id}"

    gene_info, seq_info = await asyncio.gather(
        fetch_json(session, gene_url),
        fetch_json(session, seq_url)
    )

    if gene_info:
        return {
            "gene_id": gene_info.get("id"),
            "gene_name": gene_info.get("display_name"),
            "description": gene_info.get("description"),
            "biotype": gene_info.get("biotype"),
            "location": gene_info.get("location"),
            "strand": gene_info.get("strand"),
            "assembly_name": gene_info.get("assembly_name"),
            "sequence": seq_info.get("seq") if seq_info else None
        }
    return None

async def get_genes_from_go_ensembl(go_ids):
    """Fetches gene identifiers, sequences, names, and general information for a list of GO term IDs asynchronously."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        results = {}

        for go_id in go_ids:
            url = f"{ENS_BASE_URL}/xrefs/symbol/homo_sapiens/{go_id}?external_db=GO"
            tasks.append(fetch_json(session, url))

        go_results = await asyncio.gather(*tasks)

        for go_id, genes in zip(go_ids, go_results):
            if genes:
                gene_tasks = [fetch_gene_info(session, gene.get("id")) for gene in genes]
                gene_data = await asyncio.gather(*gene_tasks)
                results[go_id] = [gene for gene in gene_data if gene]  # Remove None values
            else:
                results[go_id] = f"Error fetching genes for GO ID {go_id}"

        return results
