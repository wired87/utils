import asyncio

import networkx as nx
import json

import chromadb
import ollama
from gnn.embedder import get_embedder

from utils.file import aread_json_content

# Load a sentence embedding model
embedding_model = get_embedder()

# Initialize a local ChromaDB storage
chroma_client = chromadb.PersistentClient(path="./graph_db")
collection = chroma_client.get_or_create_collection("graph_embeddings")


def graph_to_text(graph):
    """
    Convert a NetworkX graph into a structured text format for an LLM.
    The format will describe nodes, edges, and contextual relationships.
    """
    text_representation = []

    for node in graph.nodes(data=True):
        node_id, node_attrs = node
        connections = list(graph.neighbors(node_id))
        edge_info = [f"{node_id} → {neighbor} (Edge: {graph[node_id][neighbor]})" for neighbor in connections]

        node_context = f"Node {node_id}: {json.dumps(node_attrs)}\n"
        edge_context = "\n".join(edge_info) if edge_info else "No connections.\n"

        text_representation.append(node_context + edge_context)

    return "\n\n".join(text_representation)


def store_in_chromadb(graph_text):
    """
    Converts the graph representation into embeddings and stores it locally.
    """
    embedding = embedding_model.encode(graph_text).tolist()
    collection.add(documents=[graph_text], embeddings=[embedding], ids=["graph_1"])
    print("[✔] Graph stored in ChromaDB.")


def retrieve_from_chromadb(query_text):
    """
    Retrieves the most relevant stored graph structure based on a user query.
    """
    query_embedding = embedding_model.encode(query_text).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=1)

    if results["documents"]:
        return results["documents"][0][0]
    return "No relevant graph data found."


def query_llm(graph_text, question):
    """
    Query an LLM (e.g., Llama.cpp or Ollama) with structured graph knowledge.
    """
    formatted_prompt = f"Context:\n{graph_text}\n\nQuestion: {question}"

    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": formatted_prompt}])
    return response['message']['content']


# Example Usage:
if __name__ == "__main__":
    bucket = GBucket("bestbrain")

    # Create a sample graph
    data = asyncio.run(aread_json_content(dest_path))
    G = nx.node_link_graph(data)
    # Convert graph to text
    graph_text = graph_to_text(G)
    print("\n[Graph Representation for LLM]\n", graph_text)

    # Store in ChromaDB
    store_in_chromadb(graph_text)

    # Retrieve for a given question
    query = "Who does Alice know?"
    relevant_context = retrieve_from_chromadb(query)

    # Pass retrieved context to LLM
    answer = query_llm(relevant_context, query)

    print("\n[LLM Response]:", answer)
