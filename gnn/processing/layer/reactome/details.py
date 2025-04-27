from typing import Dict

from extract_data.functions.reactome.catalyst import catalyst_activity
from extract_data.functions.reactome.compartment import handle_compartment
from extract_data.functions.reactome.get_details import get_details
from extract_data.functions.reactome.has_event import handle_has_event
from extract_data.functions.reactome.io import add_io
from extract_data.functions.reactome.participants import request_participants_and_details


def process_detailed_reactome(detail_item):
    print("Filter reactome detailed 'compartment'")

    handle_compartment(detail_item)

    handle_has_event(detail_item)

    catalyst_activity(detail_item)

    # fetch info for io
    add_io(detail_item)


def request_item_details(top_lvl_item):
    print(top_lvl_item.get("stId"))
    top_lvl_item["details"]: Dict = {}

    details = get_details(top_lvl_item['stId'])
    # pp({"details": details})
    if details:
        process_detailed_reactome(details)

        top_lvl_item["pathway_node_details"] = details

    request_participants_and_details(top_lvl_item)