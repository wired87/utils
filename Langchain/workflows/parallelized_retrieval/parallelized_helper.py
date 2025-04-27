from langchain_core.load import dumps, loads



####### 1. Langchain way
def get_unique_union(documents: list[list]):
    """
    Gets that unique docs
    """
    flattened_docs = [dumps(doc) for sublist in documents for doc in sublist]
    uique_docs = list(set(flattened_docs))
    return [loads(doc) for doc in uique_docs]








