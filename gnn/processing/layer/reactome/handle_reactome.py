"""
drop:
orthologousEvent
goBiologicalProcess[schemaClass


todo
- "figure" get svg and convert to base64


Vocab:
Entities: Broad category, encompassing everything from individual molecules to complex pathways.
Interactors: A subset of entities that actively participate in a specific reaction or interaction (e.g., reactants, products, catalysts).

"""

from extract_data.functions.file.check_ds_exist import check_ds_exists
from extract_data.functions.reactome.extract_path_from_json import extract_data
from extract_data.functions.reactome.get_details import get_details
from extract_data.functions.save_data_checkpoint import save_data_checkpoint

TOP_LEVEL_HUMAN_PATHWAY_URL = "https://reactome.org/ContentService/data/pathways/top/9606"
LOCAL_PATHWAY_JSON = r"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\filtered_data\checkpoints\reactome_full_hirarchy.json"


def consumed_event(single_item):
    # del fro now since it refers to self(main).stId
    consumer_event = single_item.get("consumedByEvent", [])
    if consumer_event and isinstance(consumer_event, list) and len(consumer_event) > 0:
        for event_id in consumer_event:
            if isinstance(event_id, int or str):
                details = get_details(st_id=event_id)
                if details:
                    consumer_event.append(details)
                    consumer_event.remove(event_id)
            else:
                print("Unusual consumedByEvent - item - id:", event_id, "type:", type(event_id))


def handle_reactome():
    """
    Download all pathways for human: GET https://reactome.org/ContentService/data/eventsHierarchy/9606 -> hierarchy_path
    """
    content = check_ds_exists(LOCAL_PATHWAY_JSON)
    print(f"Found {len(content)} items")
    extract_data(data=content)

    save_data_checkpoint(
        path=r"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\filtered_data\checkpoints\reactome_extracted.json",
        content=content
    )
