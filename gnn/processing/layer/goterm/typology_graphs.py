import aiohttp

from extract_data.functions.base_request import base_request, abase_request
from extract_data.functions.goterm.urls import goterm_graph
from asgiref.sync import sync_to_async

from extract_data.functions.print_short import p


def topology_graph(item):
    url: str = goterm_graph(go_id=item["gene_ontology_id"])
    content = base_request(url)
    if content:
        item["topology_graph_json"] = content.get("topology_graph_json", {})


async def fetch_topology_graph_async(go_id, session):
    """
    Fetches the topology graph for the given GO ID.
    """
    url = await sync_to_async(goterm_graph)(go_id=go_id)
    #print("Request typograph url:", url)
    content = await abase_request(url, session)
    if content:
        p(f"Topology Graph request successful...")
        return content
    else:
        print(f"Failed to fetch topology graph for GO ID {go_id}")
        return None


async def agraph_subgraph(item, session):
    """
    Fetch and attach the topology graph for the given item.
    """
    go_id = item["gene_ontology_id"]

    try:
        content = await fetch_topology_graph_async(go_id, session)
        if content:
            print(f"Topology content legit.{content}")
            item["graph"] = content
            sub_content = await asubtypology_graph(go_id, session)
            if sub_content:
                item["subgraph"] = sub_content
        else:
            print(f"Topology graph content missing for GO ID {go_id}")
    except Exception as e:
        print(f"Error in topology_graph_async for GO ID {go_id}: {e}")



async def asubtypology_graph(item_id, session):
    try:
        url = f"https://api.geneontology.org/api/ontology/term/{item_id}/subgraph?start=0&rows=1000000"
        content = await abase_request(url, session)
        if content:
            print("Topology content legit...")
            return content
        else:
            print(f"Topology graph content missing for GO ID {item_id}")
    except Exception as e:
        print(f"Error in sub_graph_async for GO ID {item_id}: {e}")