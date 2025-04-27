from Dashboard.bot.Langchain.workflows.parallelized_retrieval.parallelized_helper import gen_multi_queries_retrieve_docs


def get_optimized_docs_langchain_way(
    vectorstore,
    question,
    docs
):
    # 1. create multi queries and get docs from each
    docs_from_queries = gen_multi_queries_retrieve_docs(
        question
    )














# My way
def get_optimized_docs(
        vectorstore,
        question,
        docs
):
    print("OPTIMIZE THE GIVEN DOCS:", docs)

    # 1. reformulate the given question 5 times
    queries_list: list = get_multy_query(question)
    if not queries_list or isinstance(queries_list, str):
        print("GENERATED QUESTION QUERIES ARE EITHER NONE OR LEN == 0 ")
        return None

    all_docs = asyncio.run(optimize_docs(queries_list, vectorstore, docs))

    # 3. Filter the 4 highest ranked and short the chunks
    return rerank_and_short_docs(
        all_docs,
        question  # todo somehow connect all gen queries to one
    )
