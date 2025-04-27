
# async #######################################
import asyncio

import aiohttp

from extract_data.functions.extract_json_base_file import aextract_base_content
from extract_data.functions.get_molecular_process_id import aget_id
from extract_data.functions.goterm import SAVE_RESULTS_GOTERM, SAVE_GOTERM
from extract_data.functions.goterm.acheck_human import acheck_human
from extract_data.functions.goterm.agocams_for_goterm import agocams_for_goterm
from extract_data.functions.goterm.get_filter_genes import aget_filter_genes
from extract_data.functions.goterm.typology_graphs import agraph_subgraph
from extract_data.functions.save_data_checkpoint import asave_data_checkpoint
append_save_url = r"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\data\filtered_data\checkpoints\term_append_save.json"


async def ahandle_goterm(final_data_dict):
    """

    :param final_data_dict:
    :param session:
    :return:
    """


    print("Handle goterms...")
    final_data_dict["go_terms"] = []
    final_data_dict["edges"] = []
    session = aiohttp.ClientSession()
    # Read the base file
    process_list, content = await aextract_base_content()  # read -> extract nodes -> return both (nodes and raw)
    print("Base file extracted...")

    async def process_item(index, item, session):
        print(f"Processing item: {index}")
        item["associated_genes"] = []
        item["gene_ontology_id"]: str = ""

        go_id = await aget_id(item)  # extract id for requests
        if not go_id:
            return None

        item["gene_ontology_id"] = go_id

        # Check if go term is present in human
        if not await acheck_human(go_id, item, session):
            print("Go term not relevant... ->")
            # todo extend to non-human organisms
            return None

        await agraph_subgraph(item, session)

        gene_id = item["gene_ontology_id"]
        associated_genes = item["associated_genes"]

        await aget_filter_genes(gene_id, associated_genes, session)

        await agocams_for_goterm(item, go_id, session)

        return item

    # Concurrently process items in the process_list
    tasks = [process_item(index, item, session) for index, item in enumerate(process_list)]
    results = await asyncio.gather(*tasks)
    print("Information successfully gathered. Save to checkpoint...")
    await asave_data_checkpoint(
        path=SAVE_RESULTS_GOTERM,
        content=results
    )
    # Filter out None results
    final_data_dict["go_terms"].extend([result for result in results if result is not None and len(results) > 0])

    # Add edges, meta, and propertyChainAxioms
    final_data_dict["edges"] = content["graphs"][0].get("edges", [])
    final_data_dict["meta"] = content["graphs"][0].get("meta", {})
    final_data_dict["propertyChainAxioms"] = content["graphs"][0].get("propertyChainAxioms", [])

    # Save data checkpoint
    await asave_data_checkpoint(
        path=SAVE_GOTERM,
        content=final_data_dict
    )

    print(f"Data saved to checkpoint: {SAVE_GOTERM}. Close session...")
    await session.close()

