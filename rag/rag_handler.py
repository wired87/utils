import asyncio
import time
from typing import List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import PineconeVectorStore
from gnn.embedder import get_embedder

from Langchain import LANGCHAIN_EMBEDS, llm
from Langchain.core.chat_template import get_chat_template
from Langchain.core.gen_answer import gen_answer
from Langchain.re_reanking import reciprocal_rank_fusion
from Langchain.retrievers.multi_query_retriever_config import TEMPLATE
from rag.transformer_embed import TEmbedder


class RagHandler:

    def __init__(self):
        self.query_embedder = get_embedder()
        self.tembedder = TEmbedder()


    async def decompose_query(self, query: str) -> list[str] or None:
        print("DECOMPOSE QUERIES...")
        try:
            chain = (TEMPLATE | llm | StrOutputParser() | (lambda x: x.split("\n")))

            queries = await chain.ainvoke({"question": query})
            print("QUERIES:", queries, type(queries))

            return queries
        except Exception as e:
            print("COULD NOT GENERATE THE DECPOMP QUERIES:", e)
            return None

    async def get_docs_from_query_optimized(self, query: str,
                                            vectorstore):  # todo 2024-06-25 14:30:57 ERROR WHILE CREATING THE DOCS FROM SINGLE QUERIES: 'text' None
        try:

            docs: List[Document] = await vectorstore.amax_marginal_relevance_search(
                query=query,
                k=4,
                fetch_k=25,  # before 40 with perfect results 30 also good results
                lambda_mult=.5
            )
            if not docs:
                print("No documents were returned.")
                return None
                # Check if 'text' is in the first document if expected to be
            if 'text' in docs[0]:
                print("Expected 'text' field not found in the documents.")
                return None
            print("docs", docs)
            return docs
        except Exception as e:
            print("ERROR WHILE CREATING THE DOCS FROM SINGLE QUERIES:", e, e.__cause__)

    async def optimize_query(self, question):
        print("Optimize query")
        _start = time.time()
        queries = await self.decompose_query(question)  # jsut if checks suiccessfully
        _end = time.time()
        print("Optimize query TIME:", _end - _start)
        return queries

    async def retrieve_reranked_docs(self, vs, queries):
        print("Getting docs from queries")
        _start = time.time()
        tasks = [self.get_docs_from_query_optimized(query, vs) for query in queries]
        docs = await asyncio.gather(*tasks)
        print("Rerank them")
        rerank_docs = await reciprocal_rank_fusion(docs)
        _end = time.time()
        print("Rerank docs TIME:", _end - _start)
        return rerank_docs

    async def get_answer(self, docs, query):
        print("Get Answer")
        _start = time.time()
        document_chain = await get_chat_template()
        response = gen_answer(
            docs,
            document_chain,
            query
        )
        _end = time.time()
        print("Get Answer TIME:", _end - _start)
        return response

    async def query_to_document_pipe(self, query, key):
        vs = PineconeVectorStore(
            index_name="bestbrain",
            namespace=key,
            embedding=LANGCHAIN_EMBEDS  # Assuming "text-embedding-3-small"
        )
        optimized_queries = await self.optimize_query(query)
        reranked_docs = await self.retrieve_reranked_docs(queries=optimized_queries, vs=vs)
        print("reranked_docs:", reranked_docs)
        return reranked_docs

    async def go_main(self, query, key):
        go_ids=[]
        docs = await self.query_to_document_pipe(query, key)
        print("Docs fetched")
        for doc in docs:
            go_ids.append(doc.get("id", None))
        return go_ids







