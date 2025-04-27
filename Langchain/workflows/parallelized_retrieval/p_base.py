"""
Few different ways on:
1. get multy queries from input
2. generate docs for them
3. rerank them into just the top n
4. return the docs
"""
from Dashboard.bot.Langchain.re_reanking import reciprocal_rank_fusion
from Dashboard.bot.Langchain.retrievers.multi_query_retriever_config import get_multy_query_langchain_way


TEMPLATE = f"""

"""

async def get_chain_from_queries(generate_queries, retriever):

    print("GET CHAIN FROM QUERIES")
    fustion_list = retriever.map(generate_queries)
    print("FUSION LIST WILL GET:", fustion_list)

    try:
        chain = generate_queries | retriever.map() | await reciprocal_rank_fusion  # or get_unique_union
        print("CHAIN CREATED:", chain)
        return chain
    except Exception as e:
        print("CHAIN GENERATION FAILED:", e)


async def base_parallelized_retrieval_process(question: str, vectorstore):
    # gen the tmaplate
    generate_queries: list[str] or None = get_multy_query_langchain_way()
    if not generate_queries:
        return None
    # 2. set the
    retrieval_rag_chain_fusion = await get_chain_from_queries(generate_queries, vectorstore.as_retriever())
    if not retrieval_rag_chain_fusion:
        return None
    print("RAG CHAIN FUSION: ", retrieval_rag_chain_fusion)
    # 3. get docs from vectorstore based on the question
    # will generate per default 4 docs / query
    docs = await retrieval_rag_chain_fusion.ainvoke({"question": question})
    print("DOCS GENERATED:", docs, type(docs))
    return retrieval_rag_chain_fusion

"""final_rag_chain = (
    {
        "context": retrieval_rag_chain_fusion,
        "question": itemgetter("question")
    }
    | get_prompt_template(TEMPLATE)
    | llm
    | StrOutputParser()
)
print("FINAL RAG CHAIN CREATED...")
response = final_rag_chain.invoke({"question": question})

return response"""




