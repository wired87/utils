from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import DocumentCompressorPipeline, EmbeddingsFilter
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_transformers import EmbeddingsRedundantFilter

from Dashboard.bot.Langchain import embeddings

# todo implement after testing directly in splitting
splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=20, separator=". ")

redundant_filter = EmbeddingsRedundantFilter(embeddingss=embeddings)

relevant_filter = EmbeddingsFilter(embeddingss=embeddings, similarity_threshold=0.76)

pipeline_compressor = DocumentCompressorPipeline(
    transformers=[splitter, redundant_filter, relevant_filter]
)

def get_embedding_compression_filter(retriever, question):

    """
    # Use of compressor and embeddings filter together
    # pros: not that expensive, best results
    # cons: just that process may take to 10 sec.
    """

    print("START COMPRESSION AND EMBEDDINGS FILTER...")

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=pipeline_compressor,
        base_retriever=retriever
    )
    print("COMPRESSION RETRIEVER CREATED:", compression_retriever)

    compressed_docs = compression_retriever.get_relevant_documents(query=question)
    print("COMPRESSED / FILTERED DOCS:", compressed_docs)

    return compressed_docs
