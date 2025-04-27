from extract_data.functions.base_request import base_request
from extract_data.functions.print_short import p


def handle_regulators(item):
    p(f"Handle regulators for item {item.get('stId')}")
    url = rf"https://reactome.org/ContentService/data/query/enhanced/{item.get('stId')}"
    content = base_request(url)
    if content:
        regulatory = content.get("regulatedBy", None)
        if regulatory:
            item["regulatedBy"] = regulatory