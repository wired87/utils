import asyncio
import os
import re
import networkx as nx
from langchain_community.chains.graph_qa.base import GraphQAChain
from langchain_community.graphs import NetworkxEntityGraph
from google.cloud import storage

from utils.file import aread_json_content
from ggoogle.storage.storage import GBucket
from gnn.main import SRC_PATH
from pathlib import Path

from rag.hybrid_rag.identify_coding_genes.get_ontology_terms import get_on_terms
from rag.hybrid_rag.identify_coding_genes.preprocess import preprocess_prompt


class HybridRag:
    def __init__(self, dest_path):
        """Initialize Hybrid RAG with query expansion, weighted retrieval, and optimized graph handling."""
        self.llm = None
        self.bucket = GBucket("bestbrain")
        self.dest_path = dest_path
        self.chain = None
        self.retrieved_data = {}  # For feedback and continuous improvement
        self.G = nx.Graph()
        self.g_utils = GraphUtils(general_stuff=SRC_PATH, G=self.G)

    async def preprocess_query(self, query):
        """Step 0: Expand the query using LLM and Gene Ontology (GO) data for improved retrieval."""
        prompt = preprocess_prompt(query)
        expanded_query = self.llm.invoke(prompt).content  # Extract response
        print(f"🔍 Expanded Query: {expanded_query}")
        return expanded_query

    async def get_chain(self, G):
        """Set up Graph Chain for Query Execution with validated graph."""
        print("🔗 Setting up Graph Chain with weighted retrieval...")

        if not G:
            raise ValueError("⚠️ Graph is not properly loaded. Ensure `load_saved_graph()` ran successfully!")
        print("G:",G)
        chain = GraphQAChain.from_llm(
            llm=self.llm,
            graph=G,
            verbose=True
        )

        return chain

    async def query(self, query, chain):
        """Run Graph Query and apply ranking for better accuracy."""
        response = chain.invoke(get_on_terms(query))
        print("response", response)
        # Rank GO-Terms by relevance if multiple results exist
        go_terms = extract_go_terms(response)
        ranked_terms = self.rank_go_terms(go_terms)

        # Store results for feedback loop
        self.retrieved_data[query] = ranked_terms

        print("📡 Ranked Response:", ranked_terms)

    async def load_saved_graph(self):
        """Step 1: Download & Load Graph from GCS (if needed) and optimize traversal."""
        BUCKET_NAME = "bestbrain"
        SOURCE_FILE = "model_graph/sne/go_term_g.json"

        if not os.path.exists(self.dest_path):
            print("📥 Downloading graph from GCS...")
            client = storage.Client()
            bucket = client.bucket(BUCKET_NAME)
            blob = bucket.blob(SOURCE_FILE)
            blob.download_to_filename(self.dest_path)
            print(f"✅ File {SOURCE_FILE} downloaded to {self.dest_path}")
        else:
            print(f"🔍 Found graph locally at {self.dest_path}")

        # Load and optimize graph structure
        data = await aread_json_content(self.dest_path)
        graph = nx.DiGraph(nx.node_link_graph(data))
        G = NetworkxEntityGraph(graph)
        print("G", type(G))
        return G

    async def main(self, query):
        """Test HybridRag with Query Expansion, Graph RAG, and Weighted Retrieval"""
        G = await self.load_saved_graph()
        #expanded_query = await self.preprocess_query(query)
        chain=await self.get_chain(G)
        await self.query(query, chain)

    def compute_edge_weight(self, edge_data):
        """Assigns a weight to edges based on relationship strength in GO Ontology."""
        if "relationship" in edge_data:
            relation = edge_data["relationship"].lower()
            if "regulation" in relation:
                return 3  # Higher priority for regulatory GO-Terms
            elif "development" in relation:
                return 2
            else:
                return 1
        return 1  # Default weight

    def rank_go_terms(self, go_terms):
        """Ranks GO-Terms based on relevance and frequency."""
        term_frequencies = {term: go_terms.count(term) for term in set(go_terms)}
        ranked_terms = sorted(term_frequencies.items(), key=lambda x: x[1], reverse=True)
        return [term for term, _ in ranked_terms]


# ✅ GO-Term Extraction Utility Function
def extract_go_terms(text):
    """Extracts and ranks all GO-Terms (GO:XXXXX) from a given string."""
    go_terms = re.findall(r'GO:\d{7}', text)  # Matches GO-Terms with 7-digit IDs
    return list(set(go_terms))  # Remove duplicates


# ✅ Running the script
LOCAL_DEST = Path(SRC_PATH["paths"]["graph"]["sne"]["local"]) / "go_term.json"
QUERY = "Return an random id from the graph you are loaded with"#"Which go_terms are involved in dendrite development?"

if __name__ == "__main__":
    hr = HybridRag(dest_path=LOCAL_DEST)
    asyncio.run(hr.main(QUERY))





import asyncio
from cachetools import TTLCache
from Langchain.pinecone import Index, NotFoundException, PineconeException, Pinecone
from Langchain.pinecone import ServerlessSpec
from langchain.embeddings import OpenAIEmbeddings

from gnn import SRC_PATH
from utils.utils import GraphUtils

# Simple TTL Cache for frequent queries
vs_cache = TTLCache(maxsize=100, ttl=3600)
pc = Pinecone(api_key="pcsk_4efGmK_3V6e4n7AW3An97zoMjNDcuHMFoj3czMwNMPJRHxHwkNyhrK3ififwTo93Df3Zbc")

class PineconeHandler:
    def __init__(self, index_name="similarity", dimension=1024, namespace="default"):
        self.index_name = index_name
        self.dimension = dimension
        self.namespace = namespace
        self.index = self.get_or_create_index()
        self.embeddings = OpenAIEmbeddings()

    def get_or_create_index(self):
        """Fetches an existing Pinecone index or creates a new one if not found."""
        try:
            return Index(self.index_name)
        except NotFoundException:
            print(f"Index {self.index_name} not found. Creating a new one...")
            self.create_index()
            return Index(self.index_name)
        except PineconeException as e:
            print(f"Error fetching index: {e}")
            return None

    def create_index(self):
        """Creates a new Pinecone index if it doesn't exist."""
        try:
            pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
            print(f"Index {self.index_name} created successfully.")
        except PineconeException as e:
            print(f"Error creating index: {e}")

    def upsert_vector(self, vector_id, text_data, metadata=None):
        """Uploads a vectorized document to Pinecone."""
        try:
            embedding = self.embeddings.embed_query(text_data)
            self.index.upsert(
                vectors=[{"id": vector_id, "values": embedding, "metadata": metadata}],
                namespace=self.namespace,
            )
            vs_cache[vector_id] = embedding
            print(f"Vector {vector_id} upserted successfully.")
        except PineconeException as e:
            print(f"Error upserting vector: {e}")

    def fetch_vector(self, vector_id):
        """Fetches a vector from Pinecone with caching."""
        if vector_id in vs_cache:
            print("Fetching from cache...")
            return vs_cache[vector_id]
        try:
            response = self.index.fetch(ids=[vector_id], namespace=self.namespace)
            vector_data = response.get("vectors", {}).get(vector_id, None)
            if vector_data:
                vs_cache[vector_id] = vector_data
            return vector_data
        except PineconeException as e:
            print(f"Error fetching vector: {e}")
            return None

    def query_vector(self, query_text, top_k=5):
        """Queries the Pinecone index using LangChain and returns the top matches."""
        try:
            query_embedding = self.embeddings.embed_query(query_text)
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace,
            )
            return results
        except PineconeException as e:
            print(f"Error querying vector: {e}")
            return None

    def delete_vector(self, vector_id):
        """Deletes a vector from Pinecone and cache."""
        try:
            self.index.delete(ids=[vector_id], namespace=self.namespace)
            if vector_id in vs_cache:
                del vs_cache[vector_id]
            print(f"Vector {vector_id} deleted successfully.")
        except PineconeException as e:
            print(f"Error deleting vector: {e}")

    def get_index_info(self):
        """Retrieves metadata about the index."""
        try:
            info = pc.describe_index(self.index_name)
            return info
        except PineconeException as e:
            print(f"Error retrieving index info: {e}")
            return None


async def create_from_nx(filename):
    """Reads JSON and uploads to Pinecone."""
    content = await aread_json_content(filename)
    g_utils = GraphUtils(general_stuff=SRC_PATH)
    G = g_utils.load_graph("GO_TERM_G")

    pinecone_handler = PineconeHandler()

    # Example: Uploading some test data
    vector_id = "sample_id"
    text_data = "This is an example text to be embedded"
    metadata = {"source": "test_data"}

    pinecone_handler.upsert_vector(vector_id, text_data, metadata)
    fetched_vector = pinecone_handler.fetch_vector(vector_id)
    print("Fetched Vector:", fetched_vector)

    # Example: Querying the index
    query_text = "Find similar content"
    results = pinecone_handler.query_vector(query_text)
    print("Query Results:", results)


def main():
    print("\nChoose an option:")
    print("1. Upload data to Pinecone")
    print("2. Query data from Pinecone")
    choice = input("\nEnter your choice (1/2): ").strip()

    pinecone_handler = PineconeHandler()

    if choice == "1":
        filename = input("\nEnter the JSON filename: ").strip()
        asyncio.run(create_from_nx(filename))
    elif choice == "2":
        query_text = input("\nEnter the query text: ").strip()
        results = pinecone_handler.query_vector(query_text)
        print("\nQuery Results:")
        for match in results.get("matches", []):
            print(f"- Score: {match['score']}, Metadata: {match.get('metadata')}")
    else:
        print("Invalid choice. Please select 1 or 2.")


if __name__ == "__main__":
    main()


