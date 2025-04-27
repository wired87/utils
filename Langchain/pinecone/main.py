
from cachetools import TTLCache
from Langchain.pinecone import Pinecone



# Simple TTL Cache for frequent queries
vs_cache = TTLCache(maxsize=100, ttl=3600)
pc = Pinecone(api_key="pcsk_4efGmK_3V6e4n7AW3An97zoMjNDcuHMFoj3czMwNMPJRHxHwkNyhrK3ififwTo93Df3Zbc")

