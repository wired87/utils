import requests


async def get_gene_seq(item, g_utils):
    server = "https://rest.ensembl.org"
    ext = f"/sequence/region/human/{item.get('coord_sys', 'X')}:{item['start']}..{item['end']}:1?"
    headers = {"Content-Type": "text/plain"}
    content = g_utils.utils.aget(url=server + ext, j=True)
    try:
        item["seq"] = content["seq"]
    except Exception as e:
        print("No seq found")

    return item