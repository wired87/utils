from extract_data.functions.base_request import base_request, abase_request


def check_human(go_id):
    url = rf"https://api.geneontology.org/api/bioentity/function/{go_id}/taxons?start=0&rows=100"
    content = base_request(url)
    if content and len(content) > 0:
        for species in content:
            if species["taxon"] == "NCBITaxon:9606":
                return True
    return False


async def acheck_human(go_id, item, session):
    item["taxon"] = {}
    item["taxon"]["id"] = ""
    item["taxon"]["label"] = ""
    print("Check human availability...")
    url = f"https://api.geneontology.org/api/bioentity/function/{go_id}/taxons?start=0&rows=100"
    content = await abase_request(url, session)
    if content:
        for species in content:
            spec_id = species.get("taxon", None)
            if spec_id == "NCBITaxon:9606":
                print("Goterm human checked ->")
                item["taxon"]["id"]= spec_id
                item["taxon"]["label"] = "Homo Sapiens"  # todo design dynamic
                return True
        print(f"GO-Term {go_id} NOT available for humans...")
    return False