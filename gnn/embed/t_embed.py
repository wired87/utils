import json
import networkx as nx
import numpy as np
from langchain_openai import ChatOpenAI
from gnn.embedder import get_embedder
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import torch
import torch.nn as nn
from pathlib import Path

class HybridRag:
    def __init__(self, dest_path, llm=None):
        """✅ Initialize Hybrid RAG"""
        self.dest_path = Path(dest_path)
        self.llm = llm if llm else ChatOpenAI(model="gpt-4", temperature=0.1)
        self.graph = None
        self.faiss_index = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.sentence_model = get_embedder()

    async def load_saved_graph(self):
        """✅ Load Graph from JSON"""
        with open(self.dest_path, "r") as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data)

    def graph_to_text(self):
        """✅ Convert Graph Metadata into Structured Text for ChatGPT"""
        texts = []
        node_ids = []
        for node, attrs in self.graph.nodes(data=True):
            text = f"Node: {node}, Type: {attrs.get('type', 'unknown')}, SubType: {attrs.get('parent', '')}, Label: {attrs.get('lbl', '')}, Definition: {attrs.get('meta.definition.val', '')}"
            texts.append(text)
            node_ids.append(node)
        return node_ids, texts

    def generate_embeddings(self):
        """✅ Generate ChatGPT-compatible embeddings using Hugging Face"""
        node_ids, texts = self.graph_to_text()
        embeddings = self.sentence_model.encode(texts, convert_to_numpy=True)
        return node_ids, embeddings

    def store_embeddings_in_faiss(self):
        """✅ Store Embeddings in FAISS"""
        node_ids, embeddings = self.generate_embeddings()
        faiss_index = FAISS.from_embeddings(embeddings, OpenAIEmbeddings())  # Can replace with local embedding model
        faiss_index.save_local("faiss_graph_index")
        self.faiss_index = faiss_index
        print("✅ FAISS index stored!")

    def query(self, query_text):
        """✅ Query FAISS and Pass Results to LLM"""
        similar_nodes = self.faiss_index.similarity_search(query_text, k=5)
        context = "\n".join([f"{node.metadata['text']}" for node in similar_nodes])

        prompt = f"Answer based on the graph data:\n\nContext:\n{context}\n\nQuestion: {query_text}"
        response = self.llm.invoke(prompt)
        return response
