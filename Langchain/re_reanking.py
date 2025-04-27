import time

from langchain_core.load import loads, dumps


"""
RAG fusion it the part where the optimized docs are been taken and get reranked. 
The function below will per default return the top 6 ( highest ranked ) docs
"""

async def reciprocal_rank_fusion(results: list, k=60):
    """Reciprocal_rank_fusion that takes multiple lists of ranked documents
    and an optional parameter k used in the RRF formula

    It returns the top unique ranked documents
    """
    start = time.time()
    fused_scores = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            # Convert the document to a string format to use as a key (assumes documents can be serialized to JSON)
            doc_str = dumps(doc)
            if doc_str not in fused_scores:
                fused_scores[doc_str] = 0

            fused_scores[doc_str] += 1 / (rank + k)

    # Sort the documents based on their fused scores in descending order to get the final reranked results

    top_k_docs = [loads(doc) for doc, _ in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:k]]

    # Return the reranked results as a list of tuples, each containing the document and its fused score
    print("DOCS SUZCCESSFUL RERANKED...")

    end = time.time()
    print("DOCS SUCCESSFULLY RERANKED - TIME:", end - start)

    return top_k_docs


"""
def switch_data_pc_vs(vectorstore, data):
    print("SWITCH DATA IN VS...")

    vectorstore = vectorstore.delete(delete_all=True)
    vectorstore= get_pc_vector_store()
    
"""