from dotenv import load_dotenv

load_dotenv()

"""
pip install pinecone-client
"""

pc = None
# todo when get index filter for host instead for name:
"""
 pc = Pinecone(
    api_key=os.environ.get("PINECONE_API_KEY")
)

host = pc.describe_index('index-name').host
"""


