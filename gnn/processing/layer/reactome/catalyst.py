from extract_data.functions.print_short import p
from extract_data.functions.reactome.get_details import get_details
from extract_data.functions.save_data_checkpoint import save_data_checkpoint


def catalyst_activity(item):
    catalyst = item.get("catalystActivity", None)
    if catalyst and isinstance(catalyst, list) and len(catalyst) > 0:
        for k, i in enumerate(catalyst):
            i["catalyst_detail"] = {}
            p(f"Working catalyst item: {k}...")
            content = get_details(st_id=item["dbId"])
            if content:
                i["catalyst_detail"] = content
    save_data_checkpoint(
        path=r"C:\Users\wired\OneDrive\Desktop\Projects\aws_to_bucket\extract_data\filtered_data\checkpoints\catalyst.json",
        content=catalyst
    )
