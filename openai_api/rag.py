
from openai_api import client
def create_vs(name):
    vector_store = client.vector_stores.create(        # Create vector store
        name=name,
    )
def upload_file(vector_store):
    client.vector_stores.files.upload_and_poll(        # Upload file
        vector_store_id=vector_store.id,
        file=open("customer_policies.txt", "rb")
    )