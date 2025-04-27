import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from gnn import SRC_PATH
from Langchain.pinecone.vectorstore import PCVectorStore


from gnn.embedder import get_embedder


async def pc_index_from_graph(
        index=None,
        index_name="bestbrain",
        namespace="go_term"
):
    """Retrieves the Pinecone VectorStore for querying."""

    pcvs = PCVectorStore()

    # Get or create index
    if not index:
        index = await pcvs.aget_index(index_name)
        if index is None:
            return None

    # Initialize Pinecone VectorStore
    """vs = PineconeVectorStore(
        index_name=index.name,
        namespace=namespace,
        embedding="LANGCHAIN_EMBEDS"  # Assuming "text-embedding-3-small"
    )
    return vs"""


async def query_graph_vectorstore(
        query: str,
        top_k: int = 15,
        b_path=f"{SRC_PATH['paths']['graph']['sne']['bucket']}/rag/",
        namespace="go_term.json",
        index_name="bestbrain",
        t="gcp"
):
    """
    Queries Pinecone to retrieve relevant documents based on a text query.

    :param query: The text query for similarity search.
    :param top_k: Number of top results to return.
    :param namespace: The namespace to query within the index.
    :param index_name: The Pinecone index to use.
    :return: List of retrieved documents.
    """



    if t=="gcp":
        query_embed = get_embedder().encode(query)
        embeddings_dict = {}
        keys = list(embeddings_dict["embeds"].keys())  # Document names
        vectors = np.array(list(embeddings_dict["embeds"].values()))
        similarities = cosine_similarity([query_embed], vectors)[0]
        most_similar_index = np.argmax(similarities)  # Index of the highest similarity
        most_similar_doc = keys[most_similar_index]  # Get the corresponding document

        print(f"Most similar document: {most_similar_doc}, Similarity: {similarities[most_similar_index]:.4f}")
