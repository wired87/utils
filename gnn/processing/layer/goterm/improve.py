import asyncio

import aiohttp

from extract_data.functions.gocam.gocom import read_json_content_async
from extract_data.functions.goterm.agocams_for_goterm import agocams_for_goterm
from extract_data.functions.goterm.get_filter_genes import aget_filter_genes
from extract_data.functions.goterm.metadata import metadata_term
from extract_data.functions.goterm.typology_graphs import agraph_subgraph
from extract_data.functions.save_data_checkpoint import asave_data_checkpoint

gocam = r"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\data\filtered_data\checkpoints\gocam.json"
goterm = r"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\data\filtered_data\checkpoints\goterm.json"
terms_to_append = []
append_save_url = r"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\data\filtered_data\checkpoints\term_append_save.json"
additional_terms = r"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\data\filtered_data\checkpoints\additional_terms.json"


async def check(term_content, itypeitems):
    try:
        for term_item in term_content["go_terms"]:
            # check if each goterm exist
            #print("Check", term_item["gene_ontology_id"])
            if term_item["gene_ontology_id"] == itypeitems["id"]:
                return True
    except Exception as e:
        print(f"error: {e} occurred... itypeitems", itypeitems)
        await asyncio.sleep(10)



async def improve_goterm_list():
    content = await read_json_content_async(path=gocam)
    term_content = await read_json_content_async(path=goterm)
    if content:
        for item in content["human_gomodel"].items():
            model_id, model_details = item
            #print("model_id: " + model_id)
            individuals = model_details.get('individuals', None)
            if individuals:
                for individual in individuals:
                    # ref singl individual
                    itype = individual.get('type', [])
                    for itypeitems in itype:
                        # check if goterm object exist
                        filter_key =  itypeitems.get("filler", None)
                        if filter_key:
                            item_exist = await check(term_content, filter_key)
                            if not item_exist:
                                print(f"Goterm in type does not exist...")
                                terms_to_append.append(filter_key["id"])
                        else:
                            item_exist = await check(term_content, itypeitems)
                            if not item_exist:
                                print(f"Goterm in type does not exist...")
                                terms_to_append.append(itypeitems["id"])

                    root_type = individual.get('root-type', [])
                    if len(root_type)>0:
                        for rt in root_type:
                            item_exist = await check(term_content, rt)
                            if not item_exist:
                                print(f"Goterm in root_type does not exist...")
                                terms_to_append.append(rt["id"])
    await asave_data_checkpoint(path=append_save_url, content=terms_to_append)




async def work(item, session):
    extracted_item = {}
    go_metadata = await metadata_term(item=item, session=session)
    if go_metadata:
        extracted_item["gene_ontology_id"] = go_metadata["goid"]
        extracted_item["lbl"] = go_metadata["label"]
        extracted_item["meta"] = {
            "definition": {
                "val": "",
                "xrefs": []
            },
            "synonyms": []
        }
        extracted_item["meta"]["definition"]["val"] = go_metadata["definition"]
        stuff = go_metadata.get("synonyms", [])
        extracted_item["meta"]["synonyms"] = [{
            "pred": "hasExactSynonym",
            "val": item_def,
            "xrefs": []
        } for item_def in stuff if len(stuff) > 0]

        extracted_item["subsets"] = go_metadata["subsets"]
        extracted_item["relatedSynonyms"] = go_metadata.get("relatedSynonyms")
        extracted_item["alternativeIds"] = go_metadata.get("alternativeIds")
        extracted_item["xrefs"] = go_metadata.get("xrefs")

    await agraph_subgraph(extracted_item, session)
    extracted_item["associated_genes"] = []
    await aget_filter_genes(extracted_item["gene_ontology_id"], item["associated_genes"], session)

    await agocams_for_goterm(extracted_item, extracted_item["gene_ontology_id"], session)


async def handle_missing():
    session = aiohttp.ClientSession()
    content = await read_json_content_async(path=append_save_url)
    if content:
        tasks = [work(item, session) for index, item in enumerate(content) if "GO:" in item]
        results = await asyncio.gather(*tasks)
        print("Information successfully gathered. Save to checkpoint...")
        await asave_data_checkpoint(
            path=additional_terms,
            content=results
        )
    await session.close()

"""
SINGLE INDIVIDUAL
{
          "id": "gomodel:666b894f00002043/666b894f00002044",
          "type": [
            {
              "type": "class",
              "id": "GO:0004993",
              "label": "G protein-coupled serotonin receptor activity"
            }
          ],
          "root-type": [
            {
              "type": "class",
              "id": "GO:0003674",
              "label": "molecular_function"
            },
            {
              "type": "class",
              "id": "obo:go/extensions/reacto.owl#molecular_event",
              "label": "Molecular Event"
            }
          ],
          "annotations": [
            {
              "key": "date",
              "value": "2024-06-25"
            },
            {
              "key": "providedBy",
              "value": "https://www.uniprot.org"
            },
            {
              "key": "contributor",
              "value": "https://orcid.org/0000-0001-7299-6685"
            }
          ]
        },

"""