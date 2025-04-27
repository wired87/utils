from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from Dashboard.bot.Langchain import embeddings


def filter_question_with_embeddings(question, retriever):
    """
    Embedding models are cheaper and faster then the normal way (!if they are right used!).
    """
    print("BEGIN FILTER THE QUESTION...")
    embeddings_filter = EmbeddingsFilter(
        embeddings=embeddings,
        similarity_threshold=0.75 # .99 = no query anymore out .5 = no changes
    )
    print("EMBEDDING FILTER CREATED:", embeddings_filter)

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=embeddings_filter,
        base_retriever=retriever
    )
    print("COMPRESSION RETRIEVER CREATED:", compression_retriever)

    compressed_docs = compression_retriever.get_relevant_documents(query=question)
    print("DOCS COMPRESSED:", compressed_docs)
    return compressed_docs