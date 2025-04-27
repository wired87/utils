import os

from dotenv import load_dotenv
from datetime import datetime
from apify_client import ApifyClient

# setup
load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

apify_client = ApifyClient(APIFY_API_TOKEN)

time = datetime.utcnow().isoformat()

CREATE_BOT_URL = 'https://wired66.pythonanywhere.com/bot/create-process/'
DISABLE_BOT_URL = 'https://wired66.pythonanywhere.com/bot/disable/'


