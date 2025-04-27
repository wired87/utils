import argparse

import aiohttp

from agents.data_agent.docker.base_request import abase_request
INFO_NEED= [
    "node",
    "edge",
]
import pandas as pd
import pyarrow.parquet as pq
import xml.etree.ElementTree as ET
from google.cloud import storage

BUCKET_NAME = "your-gcs-bucket"  # Change to your Cloud Storage bucket
OUTPUT_FOLDER = "processed_csv"

def convert_to_csv(input_path, file_type):
    """ Converts various file formats to CSV """
    if file_type == "json":
        df = pd.read_json(input_path)
    elif file_type == "parquet":
        table = pq.read_table(input_path)
        df = table.to_pandas()
    elif file_type == "xml":
        tree = ET.parse(input_path)
        root = tree.getroot()
        data = [{elem.tag: elem.text for elem in item} for item in root]
        df = pd.DataFrame(data)
    elif file_type in ["xlsx", "xls"]:
        df = pd.read_excel(input_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    csv_output_path = input_path.replace(file_type, "csv")
    df.to_csv(csv_output_path, index=False)
    return csv_output_path

def process_files():
    """ Fetch files from GCS, convert, and save back """
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix="raw_data/")

    for blob in blobs:
        file_type = blob.name.split('.')[-1]
        if file_type not in ["json", "parquet", "xml", "xlsx", "xls"]:
            continue  # Skip unsupported formats

        local_file_path = f"/tmp/{blob.name.split('/')[-1]}"
        blob.download_to_filename(local_file_path)
        csv_path = convert_to_csv(local_file_path, file_type)

        # Upload to processed folder
        new_blob = bucket.blob(f"{OUTPUT_FOLDER}/{csv_path.split('/')[-1]}")
        new_blob.upload_from_filename(csv_path)
        print(f"Converted {blob.name} -> {new_blob.name}")

if __name__ == "__main__":
    process_files()


async def process_ds_content(content, file_type):
    chunk_size = 5 * 1024 * 1024

    chunk = content[:chunk_size]
    for need in INFO_NEED:
        return


async def main(urls):
    session = aiohttp.ClientSession()

    for ds_url in urls:
        print("Fetch ds url: %s" % ds_url)
        file_type = ds_url.strip(".")[-1]
        content = await abase_request(
            url=ds_url,
            session=session,
            request_type=file_type
        )
        await process_ds_content(content, file_type)



if __name__ == "__main__":
    """
    WORKS FOR NOW JUST WITH FASTA, XML AND CSV
    """
    parser = argparse.ArgumentParser(description="Process some arguments.")
    parser.add_argument("--urls", type=str, nargs='+', required=True, help="urls to the datasets in csv or xml format")

    args = parser.parse_args()
    main(args.uls)