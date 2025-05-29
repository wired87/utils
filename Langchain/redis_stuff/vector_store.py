from typing import List, Optional

from langchain_community.vectorstores.redis import Redis
from langchain_core.documents import Document

from Dashboard.bot.Langchain import embeddings
from chat_bot_webite.settings import REDIS_BROKER_URL
"""
    Redis.__init__.py - Initialize directly
    Redis.from_documents - Initialize from a list of Langchain.docstore.Document objects
    Redis.from_texts - Initialize from a list of texts (optionally with metadata)
    Redis.from_texts_return_keys - Initialize from a list of texts (optionally with metadata) and return the keys
    Redis.from_existing_index - Initialize from an existing Redis index
    """

def create_vector_store__from_text(
        texts: List[str],
        metadata: Optional[List[dict]] = None,
        index_name: Optional[str] = None
) -> Redis or None:

    try:

        rds = Redis.from_texts(
            texts,
            embeddings,
            metadatas=metadata,
            redis_url=REDIS_BROKER_URL,
            index_name=index_name,
        )

        print("REDIS VECTOR STORE CREATED...")

        return rds

    except Exception as e:
        print("ERROR OCCURRED WHILE CREATING REDIS VECTOR STORE: ", e)
    return None


def create_vector_store_from_docs(
        docs: List[Document],
        metadata: Optional[List[dict]] = None,
        index_name: Optional[str] = None
) -> Redis or None:
    """
    pip install redis redisvl

    """
    print("TRY CREATE THE VECTORSTORE...")
    try:
        rds = Redis.from_documents(
            docs,
            embeddings,
            #metadatas=metadata,
            redis_url=REDIS_BROKER_URL,
            index_name=index_name,
        )

        print("REDIS VECTOR STORE FROM DOCS CREATED...")

        return rds

    except Exception as e:
        print("ERROR OCCURRED WHILE CREATING REDIS VECTOR STORE: ", e)
    return None
