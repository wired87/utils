from extract_data.functions.base_request import base_request


def get_details(st_id: str or None = None, url: str or None = None):
    if not url and st_id:
        url = f"https://reactome.org/ContentService/data/query/{st_id}"
    details = base_request(url)
    return details