"""
done:
convert to async best possiboel optiized
terms linkd to gocam

todo
Goterms data ready
reactoe check, improve, debug
- if goterm not annotated to huiman -> delete
# check additional

link gocam and goterm both ways

Workflow
load json file
loop thorugh objects
extract id


Tree2:
uniprot (incl gene) ->
- goterm for gene_id
- - reactome
- gocam for gene id
- -



Tree:
Terms
- Gene
- - UniProt gene entries

- Cams
- - Gene Product



"""
import pprint
from typing import List

from extract_data.functions.extract_json_base_file import extract_base_content, aextract_base_content
from extract_data.functions.goterm import SAVE_GOTERM
from extract_data.functions.goterm.acheck_human import check_human, acheck_human
from extract_data.functions.goterm.get_filter_genes import get_filter_genes, aget_filter_genes
from extract_data.functions.get_molecular_process_id import get_id, aget_id
from extract_data.functions.goterm.typology_graphs import topology_graph, agraph_subgraph
from extract_data.functions.print_short import p
from extract_data.functions.save_data_checkpoint import save_data_checkpoint, asave_data_checkpoint






def handle_goterm(final_data_dict):
    print("Handle goterms...")
    final_data_dict["go_terms"]: List = []
    final_data_dict["edges"] = []
    #read the base file
    process_list, content = extract_base_content()
    p("Base file extracted...")

    for index, item in enumerate(process_list):
        pprint.pp({"WORKING ITEM": f"{index}"})

        go_id: str or None = get_id(item)
        if not go_id:
            continue
        item["gene_ontology_id"] = go_id

        # go term present in human?
        human = check_human(go_id)
        if not human:
            continue

        topology_graph(item)

        item["associated_genes"] = []

        get_filter_genes(item["gene_ontology_id"], item["associated_genes"])  # finished -> need test in cloud - expensive

        final_data_dict["go_terms"].append(item)
        p(f"Updated len: {len(final_data_dict)}")
        p(f"Added object: {len(final_data_dict)}")

    final_data_dict["edges"] = content["graphs"][0].get("edges")
    final_data_dict["meta"] = content["graphs"][0].get("meta")
    final_data_dict["propertyChainAxioms"] = content["graphs"][0].get("propertyChainAxioms")

    save_data_checkpoint(
        path=SAVE_GOTERM,
        content=final_data_dict
    )


