
import requests

from utils.apify import APIFY_API_TOKEN, apify_client


def rename_dataset(dataset_id, dataset_name=None):
    """Rename the dataset using the Apify API."""
    print("TESTPRINT -> :::")
    # check for double dataset['name']
    print("TRY RENAME THE DATASET TO NAME:", dataset_name)
    url = f'https://api.apify.com/v2/datasets/{dataset_id}'
    headers = {'Authorization': f'Bearer {APIFY_API_TOKEN}', 'Content-Type': 'application/json'}
    data = {'name': dataset_name}
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Dataset renamed successfully")
    else:
        print("Failed to rename dataset:", response.text)


def run_actor(url: str, webhook: list) -> dict or None:
    print("CREATE THE ACTOR TASK...")
    try:
        actor_run = apify_client.actor("apify/website-content-crawler").call(
            run_input={
                "startUrls": [{"url": url}],
                "maxRequestsPerCrawl": 1000,
            },
            webhooks=webhook,
        )
        print("ACTOR RUN RESULT:", actor_run)
        print("DATASET ID:", actor_run["defaultDatasetId"])
        return actor_run
    except Exception as e:
        print("ERROR WHILE ACTOR RUN OCCURRED:", e)
        return None




def save_instances(apify_data_model, ds_id, ds_name):
    print("SAVING ALL INSTANCES... ")

    if apify_data_model.dataset_id:
        # 1
        print("RENEWAL PROCESS -> DELETE THE OLD DATASET...")
        rename_dataset(apify_data_model.dataset_id, None)

    rename_dataset(ds_id, ds_name)

    apify_data_model.dataset_id = ds_id
    apify_data_model.save()

