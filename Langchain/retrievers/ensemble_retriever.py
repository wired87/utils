from typing import List

from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document


async def get_docs_from_ensemble_retriever(
        question: str,
        retriever,
        docs: List[Document],
        k: int = 2
) -> List[Document]:
    """
    pip install rank_bm25
    Uses bm25 (which is very good in filtering keywords) algorithm's to filter the best documents from the given docs
    """
    print("CREATE ENSEMBLE RETRIEVER...")
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = k  # will return k possible matched ds

    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, retriever],
        weights=[
            0.5,
            0.5
        ]  # 1. element + 2. element = 1
    )
    rel_docs = await ensemble_retriever.aget_relevant_documents(query=question)
    print("FILTERED DOCS: ", rel_docs)

    return rel_docs
