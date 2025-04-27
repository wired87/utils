from extract_data.functions.print_short import p
from extract_data.functions.reactome import detail_enhanced
from extract_data.functions.reactome.get_details import get_details


def handle_has_event(item):
    print("--- Start Handle Event ---")
    has_event = item.get("hasEvent", None)
    if has_event and isinstance(has_event, list) and len(has_event) > 0:
        for k, i in enumerate(has_event):
            p(f"Working hasEvent item: {k}...")
            item_id = i.get('stId')
            if item_id:
                p(f"ID '{item_id}' valid...")
                details = get_details(url=detail_enhanced(item_id))
                if details:
                    i["event_details"] = details
            else:
                p(f"Given ID '{item_id}' NOT VALID...")
