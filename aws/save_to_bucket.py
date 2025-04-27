import os
import pickle

import boto3

TASK_LIST = [
    'task1',
    "task2",
    "task3",
    "taskNRv2"
]

def save_local_files_from_s3(s3, bucket_name, s3_uri, path): # todo for every doenloD THE EXISITNG WILL BE REPLACED:  DOES NOT COME FROM LOCAL FILE DIR
    try:
        print("Get Files from s3...")
        paginator = s3.get_paginator('list_objects_v2')
        print("paginator set...")

        s3_path_parts = s3_uri.replace("s3://", "").split("/", 1)
        bucket_name = s3_path_parts[0]
        s3_prefix = s3_path_parts[1] if len(s3_path_parts) > 1 else ""

        for page in paginator.paginate(Bucket=bucket_name, Prefix=s3_prefix):
            print("page", page)
            for obj in page.get('Contents', []):
                s3_key = obj['Key']  # example pickled_ZuCo/pickled_sum/task1-SR-dataset.pickle
                if not s3_key.endswith('/'):
                    if os.path.exists(os.path.join(path, s3_key)):
                        continue

                    local_file_path = os.path.join(path, s3_key.replace(s3_prefix, ""))
                    print("local_file_path", local_file_path)
                    local_file_dir = os.path.dirname(local_file_path)
                    print("local_file_dir", local_file_dir)

                    if not os.path.exists(local_file_dir):
                        os.makedirs(local_file_dir)

                    print(f"Downloading {s3_key} to {local_file_path}...")
                    try:
                        s3.download_file(bucket_name, s3_key, local_file_path)
                    except Exception as e:
                        print(f"Error downloading {s3_key}: {e}")
    except Exception as e:
        print("Could not download cause:", e)


def check_ds_dir(
        path,
        bucket_name: str = "briandecodertext",
        s3_uri: str = "s3://briandecodertext/pickled_ZuCo/pickled_sum/",

):
    if os.path.exists(path):
        if len(os.listdir(path)) > 0:
            print("ITEMS IN EXISTING DS PICKLE PATH...")
            return
    else:
        os.mkdir(path)
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id='AKIAZQBRZAHPYY7FVF5W',  # todo !!!
            aws_secret_access_key='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',
            region_name='eu-central-1'
        )

        save_local_files_from_s3(s3, bucket_name, s3_uri, path)

    except Exception as e:
        print("File not found...", e)


def get_ds_path(task_name, path):
    dir_items = os.listdir(path)
    for item in dir_items:
        print("CHECKING PATH:", item)
        if os.path.isdir(item):
            print("")
            new_path = os.path.join(path, item)
            get_ds_path(task_name, new_path)
        else:
            if task_name in item:
                item_path = os.path.join(path, item)
                print("ITEM PATH SET. RETURN...")
                return item_path


def get_iterable_dict(task_name: str):
    local_path = None
    whole_dataset_dicts = []
    for task in TASK_LIST:
        if task in task_name:
            try:
                print(f"PREPARE DS {task}...")
                check_ds_dir(local_path)
                ds_path = get_ds_path(task, local_path)
                print("DATASET PATH:", ds_path)
                if not ds_path:
                    return None
                with open(ds_path, 'rb') as handle:
                    print("handle:", handle)
                    data = pickle.load(handle)
                    print("DATA:", type(data), len(data))
                    whole_dataset_dicts.append(data)
            except Exception as e:
                print(
                    "ERr",
                    e)
    return whole_dataset_dicts