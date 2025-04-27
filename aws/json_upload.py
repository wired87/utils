
import boto3
from datetime import datetime

import requests
import os
import gzip
import json
# Load environment variables from the .env file
ACCESS_ID="e3MtOEpYNMaqx+fmHGJCAKk8MrtwDTgFl5GWF53X"
SECRET_KEY="AKIAZQBRZAHPYY7FVF5W"
REGION="eu-central-1"
BUCKET="genexfabric"

# Access environment variables
aws_access_key_id = ACCESS_ID
aws_secret_access_key = SECRET_KEY
region_name = REGION
bucket_name = BUCKET

# Validate environment variables
if (
    not aws_access_key_id
    or not aws_secret_access_key
    or not region_name
    or not bucket_name
):
    print("Error: Missing required environment variables. Check your .env file.")
    exit(1)

# Initialize S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name,
)


url = "https://explore.data.humancellatlas.org/projects/005d611a-14d5-4fbf-846e-571a1f874f70/get-curl-command"
dest = "/genius.json"

# Fetch the file
response = requests.get(url)
response.raise_for_status()  # Raise an error if the request fails

# Temporary filename for decompression
temp_gz_file = "temp_ontologies.json.gz"

# Save the gzip file locally
with open(temp_gz_file, "wb") as temp_file:
    temp_file.write(response.content)

# Decompress the gzip file
with gzip.open(temp_gz_file, "rt", encoding="utf-8") as gz_file:
    decompressed_data = json.load(gz_file)

# Write decompressed JSON to the destination file
with open(dest, "w") as file:
    json.dump(decompressed_data, file, indent=2)

# Cleanup: Remove the temporary gzip file
os.remove(temp_gz_file)

print(f"Decompressed JSON saved to '{dest}'")


# Generate folder name with current date and time
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
folder_name = f"json_gene_data_{current_datetime}/"

# Get all JSON files in the current directory
json_files = [file for file in os.listdir("../extract_data/functions/cell") if file.endswith(".json")]

if not json_files:
    print("No JSON files found in the current directory.")
else:
    print(
        f"Uploading {len(json_files)} JSON files to S3 bucket '{bucket_name}' in folder '{folder_name}'..."
    )
    for json_file in json_files:
        # Create the S3 object key (folder name + file name)
        s3_key = folder_name + json_file

        try:
            # Upload the file to S3
            s3.upload_file(
                Filename=json_file,  # Local file name
                Bucket=bucket_name,  # S3 bucket name
                Key=s3_key,  # S3 key (path in the bucket)
            )
            print(f"Uploaded: {json_file} to s3://{bucket_name}/{s3_key}")
        except Exception as e:
            print(f"Failed to upload {json_file}: {e}")

print("Upload process completed.")
