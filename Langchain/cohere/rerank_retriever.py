from typing import List

from langchain_community.embeddings import CohereEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_core.documents import Document
from langchain_cohere import CohereRerank

compressor = CohereRerank()


def rerank_and_short_docs(split_docs: List[Document], query: str):
    retriever = FAISS.from_documents(
        split_docs,
        CohereEmbeddings()).as_retriever(search_kwargs={"k": 4})

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=retriever
    )
    compressed_docs = compression_retriever.invoke(query)
    print(f"{len(compressed_docs)} DOCS RE RANKED...")
    print("COMPRESSED DOCS: ", compressed_docs)
    return compressed_docs



"""

def get_optimized_docs(
    vectorstore,
    question,
    docs
):
    print("OPTIMIZE THE GIVEN DOCS:", docs)

    # 1. reformulate the given question 5 times
    queries: list = get_multy_query(question)
    if not queries or isinstance(queries, str):
        print("GENERATED QUESTION QUERIES ARE EITHER NONE OR LEN == 0 ")
        return None

    all_docs = asyncio.run(optimize_docs(queries, vectorstore, docs))

    # 3. Filter the 4 highest ranked and short the chunks
    return rerank_and_short_docs(
        all_docs,
        question  # todo somehow connect all gen queries to one
    )
"""