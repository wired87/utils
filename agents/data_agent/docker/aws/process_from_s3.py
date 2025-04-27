import gzip
import os
import boto3

ACCESS_ID="e3MtOEpYNMaqx+fmHGJCAKk8MrtwDTgFl5GWF53X"
SECRET_KEY="AKIAZQBRZAHPYY7FVF5W"
REGION="eu-central-1"
BUCKET="genexfabric"

# Access environment variables
aws_access_key_id = ACCESS_ID
aws_secret_access_key = SECRET_KEY
region_name = REGION
bucket_name = BUCKET

s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )

def process_gz_file(gz_file_key, json_file_key):
    try:
        # Step 1: Download the .gz file from S3
        local_gz_file = "/tmp/temp_file.gz"
        local_json_file = "/tmp/temp_file.json"
        print(f"Downloading {gz_file_key} from bucket {BUCKET}...")
        s3.download_file(BUCKET, gz_file_key, local_gz_file)

        # Step 2: Unzip the .gz file
        print(f"Unzipping {gz_file_key}...")
        with gzip.open(local_gz_file, 'rb') as gz_file:
            with open(local_json_file, 'wb') as json_file:
                json_file.write(gz_file.read())

        # Step 3: Upload the extracted JSON file back to S3
        print(f"Uploading extracted JSON file to {json_file_key} in bucket {bucket_name}...")
        s3.upload_file(local_json_file, BUCKET, json_file_key)

        # Cleanup local files
        os.remove(local_gz_file)
        os.remove(local_json_file)

        print("Process completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

dest = "/home/ec2-user/work/ontologies_linked.json.gz"

if __name__ == "__main__":
    process_gz_file("ontologies_linked.json.gz", dest)
