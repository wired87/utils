# EXPENSIVE BECAUSE EVERY DOCUMENT MUST BE SHORTED BY THE LLM BEFORE THE QUESTION ASNWERING PROCESS STARTS
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

from Dashboard.bot.Langchain.chat_preparation import llm

compressor = LLMChainExtractor.from_llm(llm)


def compress_docs(retriever, question, base_compressor=compressor):
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=base_compressor,
        base_retriever=retriever
    )

    compressed_docs = compression_retriever.get_relevant_documents(query=question)
    print("COMPRESSED DOCS:", compressed_docs)

    return compressed_docs
