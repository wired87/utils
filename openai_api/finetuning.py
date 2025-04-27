"""
gpt-4o-2024-08-06
gpt-4o-mini-2024-07-18
gpt-4-0613
gpt-3.5-turbo-0125
gpt-3.5-turbo-1106
gpt-3.5-turbo-0613
"""
from openai_api import client

job = client.fine_tuning.jobs.create(
    training_file="file-all-about-the-weather",
    model="gpt-4o-2024-08-06",
    method={
        "type": "dpo",
        "dpo": {
            "hyperparameters": {"beta": 0.1},
        },
    },
)