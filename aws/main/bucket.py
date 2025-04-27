import datetime
import json
import os
from glob import glob
from typing import Type
"""
import boto3
import h5py
import scipy.io as io
from botocore.exceptions import NoCredentialsError

from cloud.AWS import ACCESS_ID, SECRET_KEY, REGION


class AWSBucket:

    def __init__(
            self,
            user_id: str,
            bucket_name: str,
    ):
        self.bucket_name = bucket_name
        self.access_key_id = ACCESS_ID
        self.secret_access_key = SECRET_KEY
        self.region = REGION
        self.prefix = f"{user_id}/active" # -> if user del dataset it comes to the del folder
        self.s3_uri = f"s3://{bucket_name}/{self.prefix}/"
        self.client = self.get_client()

    def get_client(self):
        try:
            return boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,  # todo !!!
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region
            )
        except Exception as e:
            print("COULD NOT GET BUCKST CAUSE FOLLOWING ERROR:", e)
            return None

    def media_stream_upload(self, file_stream, folder, file_name):
        upload_path = f"{folder}/{file_name}"
        try:
            self.client.upload_fileobj(file_stream, self.bucket_name, upload_path)
            print(f"Successfully streamed {file_name} to {upload_path}")
        except NoCredentialsError:
            print("AWS credentials not available.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def create_file(self, s3_file_path):
        self.client.put_object(Bucket=self.bucket_name, Key=s3_file_path)

    def write_bucket(self, folder_name, file_name, eeg_data):
        s3_key = f"{folder_name}/{file_name}"

        try:
            # Fetch the existing content
            response = self.client.get_object(Bucket=self.bucket_name, Key=s3_key)
            existing_content = response['Body'].read().decode('utf-8')

            # Append data stream to existing content
            updated_content = json.loads(existing_content)
            if isinstance(updated_content, list):
                # write new values
                for item, key in self.bucket["eeg_content"].items():
                    # upload last 300 entries of each key field
                    updated_content.extend(self.bucket["eeg_content"][key:300])
            else:
                print("Existing content is not a list, unable to stream-write.")
                return

            # Write updated content back to S3
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(updated_content).encode('utf-8')
            )
            print(f"Stream-written data to file: {s3_key}")

        except self.client.exceptions.NoSuchKey:
            print(f"File {s3_key} does not exist.")


    def create_s3_folder(self, bucket_name, folder_name: Type[datetime.date] = datetime.time):
        s3 = self.get_client()
        s3_key = f"{folder_name}/"  # S3 treats keys ending with '/' as folders

        try:
            # Create an empty object to simulate folder creation
            s3.put_object(Bucket=bucket_name, Key=s3_key)
            print(f"Folder '{folder_name}' created successfully in bucket '{bucket_name}'")
        except Exception as e:
            print(f"Error creating folder '{folder_name}': {e}")


    def create_file(self):
        return


    def save(self):
        print("Saving...")

    def get_bucket_item_from_key(self, s3_key:str, s3):
        try:
            # Read the file content directly from S3
            response = s3.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            # Process the file content
            print(f"Processing content of {s3_key}...")
            # Here you can add your processing logic
            return content # For example, just printing the content
        except Exception as e:
            print(f"Error reading {s3_key}: {e}")
            return None


    def load_mat_content(self, response, s3_key: str or None = None):
        try:
            # Read the file content directly from S3
            file_stream = io.BytesIO(response['Body'].read())

            # Load the .mat file into a dictionary
            mat_contents = io.loadmat(file_stream, squeeze_me=True, struct_as_record=False)

            # Get the file size in bytes
            file_size_bytes = response['ContentLength']

            # Convert file size to GiB (1 GiB = 2^30 bytes)
            file_size_gib = file_size_bytes / (1024 ** 3)

            print(f"Processing content of {s3_key}...")

            # Return a dictionary with file name, size in GiB, and contents
            return {
                'file_name': s3_key,
                'file_size_gib': file_size_gib,
                'mat_contents': mat_contents
            }

        except Exception as e:
            print(f"Error reading {s3_key}: {e}")
            return None


    def get_files_from_prefix_folder(self):
      
        files = []
        try:
            s3 = self.get_client()
            paginator = s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix):
                for obj in page.get('Contents', []):
                    s3_key = obj['Key']
                    if not s3_key.endswith('/'):  # Ensures it's a file, not a folder
                        files.append(s3_key)
            return files
        except Exception as e:
            print("COULD NOT GET BUCKET DUE TO THE FOLLOWING ERROR:", e)
            return None

    def testing_process(self):
        final_mat_list = []
        matdata = None
        local_ds_patch =
        mat_files = glob(os.path.join(local_ds_patch, '*.mat'))
        for f in mat_files:
            print("FILES READ...")
            matdata = h5py.File(f, 'r')
            print("MAT DATA RECEIVED...")
            final_mat_list.append(matdata)
        return final_mat_list"""