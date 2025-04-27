import asyncio

from extract_data.functions.goterm.urls import gocams_for_goterm_url


async def agocams_for_goterm(item, go_id, session):
    """
    :param item: single item from base_goterm
    :param session:
    :return:
    """
    item["gocam_models"] = []

    url = gocams_for_goterm_url(go_id)
    #Returns GO-CAM model identifiers for a given GO term ID, e.g. GO:0008150
    content = await abase_request(url, session)
    """
    {
        "gocam": "http://model.geneontology.org/UniProt:XXXXXX",
        "title": "something"
    },
    """
    if content and isinstance(content, list) and len(content) > 0:
        item["gocam_models"] = content
        for i in item["go_models"]:
            extracted_gocam_id = i['gocam'].rsplit('/', 1)[-1]
            print("Gocam ID extracted:", extracted_gocam_id)
            i["id"] = extracted_gocam_id
            # todo later link everything in one big dataset
