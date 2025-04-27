import asyncio

from utils.file.web_tree import download_json_content, extract_tree

url = "https://www.encodeproject.org/report/?type=Experiment&status=released&control_type%21=%2A&replicates.library.biosample.donor.organism.scientific_name=Homo+sapiens&biosample_ontology.organ_slims=brain&limit=all"


def main(urls:list=[url]):

    data = asyncio.run(download_json_content(url))
    extract_tree(data)
    prompt = f"""
    Generate 
    """