import asyncio
from typing import List
import time

from langchain_core.documents import Document

from Langchain.core.chat_template import get_chat_template
from Langchain.core.gen_answer import gen_answer
from Langchain.re_reanking import reciprocal_rank_fusion
from Langchain.retrievers.multi_query_retriever_config import decompose_query
from Langchain.workflows.parallelized_retrieval.p_individually import get_docs_from_query_optimized


async def qa_pipe(
        question, vs
):

    rerank_docs=await optimize_query(question, vs)
    document_chain= await get_chat_template()
    response = gen_answer(
        rerank_docs,
        document_chain,
        question
    )
    print("Response:", response)

TEST_Q="""

"""

if __name__ == '__main__':
    asyncio.run(qa_pipe(TEST_Q))