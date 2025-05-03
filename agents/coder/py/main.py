import asyncio
import os
import ast
import networkx as nx

from utils.gnn.processing.model.main import asave_data_checkpoint
from utils.utils import GraphUtils


def create_metadata_table_query(table_name):
    return f"""
    CREATE TABLE metadata (
        id INT64 NOT NULL,
        edge_tables STRING(MAX)
    ) PRIMARY KEY (id)
    """




def get_edge_table_schema(edge_item_name, trgt_re_table, src_ref_table):
    return f"""
    CREATE EDGE TABLE {edge_item_name} (
        src_id INT64 NOT NULL,
        trgt_id INT64 NOT NULL,
    ) , INTERLEAVE IN PARENT {src_ref_table},
    CONSTRAINT FK_{edge_item_name}_src FOREIGN KEY (src_id) REFERENCES {src_ref_table} (id),
    CONSTRAINT FK_{edge_item_name}_trgt FOREIGN KEY (trgt_id) REFERENCES {trgt_re_table} (id)
    """

def create_graph_query(node_tables, edge_table_schema):
    node_tables_query = "\n".join([f"CREATE NODE TABLE {table} (id INT64 NOT NULL) PRIMARY KEY (id);" for table in node_tables])
    return f"""
    CREATE GRAPH BRAINMASTER (
        {node_tables_query}
        {edge_table_schema}
    );
    """

def get_graph_query(graph_name):
    return f"""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.GRAPH_TABLES
    WHERE GRAPH_NAME = '{graph_name}'
    """


class CodeGraphUploader:
    """
    A class to upload a NetworkX graph representing code structure to Spanner.
    """

    def __init__(self, g:GraphUtils):# db="BETSE13", inid="CODE"
        self.g = g

    def _upload_nodes(self, node_data_map):

        node_tables, _ = self.spanner_core.get_graph_tables("BRAINMASTER")

        for node_id, node_data in node_data_map.items():
            node_type = node_data.get("type", "unknown")
            label = node_data.get("label", "unknown")

            # Determine Spanner table based on node type
            if node_type == "file":
                table_name = "FILE"
            elif node_type == "function":
                table_name = "FUNCTION"
            elif node_type == "class":
                table_name = "CLASS"
            elif node_type == "import":
                table_name = "IMPORT"
            elif node_type == "importfrom":
                table_name = "IMPORTFROM"
            elif node_type == "assignment":
                table_name = "ASSIGNMENT"
            elif node_type == "if":
                table_name = "IF"
            elif node_type == "for":
                table_name = "FOR"
            elif node_type == "while":
                table_name = "WHILE"
            elif node_type == "try":
                table_name = "TRY"
            elif node_type == "return":
                table_name = "RETURN"
            elif node_type == "call":
                table_name = "CALL"
            elif node_type == "name":
                table_name = "NAME"
            elif node_type == "constant":
                table_name = "CONSTANT"
            else:
                table_name = "OTHER"

            if table_name not in node_tables:
                table_name = "OTHER"

            # Insert node into Spanner
            self.spanner_core.batch_process_rows(
                table_name=table_name,
                id_column_name="id",
                rows=[{"id": hash(node_id), "label": label}],
                adapt=None
            )

    def _upload_edges(self, edge_data_list):
        _, edge_tables = self.spanner_core.get_graph_tables("BRAINMASTER")

        for edge_data in edge_data_list:

            src_id = hash(edge_data["src"])
            trgt_id = hash(edge_data["trgt"])
            edge_type = edge_data["data"].get("type", "unknown")

            # Determine Spanner edge table based on edge type
            if edge_type == "imports_file":
                table_name = "IMPORTS_FILE"
            elif edge_type == "calls":
                table_name = "CALLS"
            elif edge_type == "contains":
                table_name = "CONTAINS"
            else:
                table_name = "OTHER_EDGE"

            if table_name not in edge_tables:
                table_name = "OTHER_EDGE"

            # Insert edge into Spanner
            self.spanner_core.batch_process_rows(
                table_name=table_name,
                id_column_name="src_id",
                rows=[{"src_id": src_id, "trgt_id": trgt_id}],
                adapt=None
            )

def extract_py_code_graph(project_folder):
    """
    Extracts Python code from a project folder and creates a NetworkX graph.
    """
    # ... (extract_py_code_graph function remains the same) ...
    graph = nx.DiGraph()  # Use DiGraph for directed edges (imports, calls, etc.)
    file_nodes = {}  # Store file nodes for edge creation






def extract_py_code_graph(project_folder):
    """
    Extracts Python code from a project folder and creates a NetworkX graph.

    Args:
        project_folder (str): Path to the project folder.

    Returns:
        nx.Graph: A NetworkX graph representing the project's code structure.
    """

    graph = nx.Graph()  # Use DiGraph for directed edges (imports, calls, etc.)
    file_nodes = {}  # Store file nodes for edge creation

    for root, _, files in os.walk(project_folder):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    tree = ast.parse(code)

                    # Create a file node
                    file_node_id = file_path
                    graph.add_node(file_node_id, type="file", label=file)
                    file_nodes[file_path] = file_node_id

                    # Extract nodes and edges from the AST
                    _extract_nodes_and_edges(graph, tree, file_node_id, file_nodes, code)

                except (SyntaxError, UnicodeDecodeError) as e:
                    print(f"Error processing {file_path}: {e}")

    _resolve_imports_and_calls(graph, file_nodes)

    return graph

def _extract_nodes_and_edges(graph, tree, file_node_id, file_nodes, code):
    """
    Recursively extracts nodes and edges from the AST.
    """

    for node in ast.walk(tree):
        node_id = f"{file_node_id}:{ast.unparse(node).strip()[:100]}"  # Unique ID, avoid very long names.
        node_label = ast.unparse(node).strip()[:100] # short label
        node_type = type(node).__name__.lower()

        if isinstance(node, ast.FunctionDef):
            graph.add_node(node_id, type="function", label=node.name)
        elif isinstance(node, ast.ClassDef):
            graph.add_node(node_id, type="class", label=node.name)
        elif isinstance(node, ast.Import):
            graph.add_node(node_id, type="import", label=ast.unparse(node))
        elif isinstance(node, ast.ImportFrom):
            graph.add_node(node_id, type="importfrom", label=ast.unparse(node))
        elif isinstance(node, ast.Assign):
            graph.add_node(node_id, type="assignment", label=ast.unparse(node))
        elif isinstance(node, ast.If):
            graph.add_node(node_id, type="if", label="if statement")
        elif isinstance(node, ast.For):
            graph.add_node(node_id, type="for", label="for loop")
        elif isinstance(node, ast.While):
            graph.add_node(node_id, type="while", label="while loop")
        elif isinstance(node, ast.Try):
            graph.add_node(node_id, type="try", label="try block")
        elif isinstance(node, ast.Return):
            graph.add_node(node_id, type="return", label="return statement")
        elif isinstance(node, ast.Call):
            graph.add_node(node_id, type="call", label=ast.unparse(node.func))
        elif isinstance(node, ast.Name):
            graph.add_node(node_id, type="name", label=node.id)
        elif isinstance(node, ast.Constant):
            graph.add_node(node_id, type="constant", label=node.value)
        else:
            graph.add_node(node_id, type=node_type, label=node_label) # add all other nodes

        if node is not tree: # Avoid connecting root to itself
            parent_id = f"{file_node_id}:{ast.unparse(getattr(node, 'parent', tree)).strip()[:100]}" # get parent id
            graph.add_edge(parent_id, node_id, type="contains") # connect to its parent

        for child in ast.iter_child_nodes(node):
            child.parent = node # add parent atribute for easier navigation
            if isinstance(child, ast.FunctionDef) or isinstance(child, ast.ClassDef):
                pass
            else:
                _extract_nodes_and_edges(graph, child, file_node_id, file_nodes, code)

def _resolve_imports_and_calls(graph, file_nodes):
    """
    Resolves imports and calls to create edges between files and nodes.
    """

    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("type") == "import" or node_data.get("type") == "importfrom":
            import_statement = ast.parse(node_data["label"]).body[0]
            module_name = import_statement.module if isinstance(import_statement, ast.ImportFrom) else import_statement.names[0].name
            # simplified import resolution: only match file name
            for file_path, file_node_id in file_nodes.items():
                if os.path.splitext(os.path.basename(file_path))[0] == module_name:
                    graph.add_edge(node_id, file_node_id, type="imports_file")
                    break

        if node_data.get("type") == "call":
            call_name = node_data.get("label")
            for other_node_id, other_node_data in graph.nodes(data=True):
                if other_node_data.get("type") == "function" and other_node_data.get("label") == call_name:
                    graph.add_edge(node_id, other_node_id, type="calls")
                    break


import functools
from typing import Callable, Optional, Any

def cache_validation(
    cache_key_prefix: str,
    validation_function: Callable[[Any], bool],
    error_message: Optional[str] = None,
) -> Callable:
    """
    Decorator to validate cached data using a given validation function.

    Args:
        cache_key_prefix: Prefix for the cache key.
        validation_function: A function that takes the cached data as input and
            returns True if the data is valid, False otherwise.
        error_message: Optional error message to raise if validation fails.

    Returns:
        A decorated function that performs cache validation.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Assuming you have a cache mechanism (replace with your actual cache)
            cache_key = f"{cache_key_prefix}:{args}:{kwargs}"  # Example cache key

            # Fetch data from cache (replace with your cache retrieval logic)
            cached_data = None  # Replace with actual cache retrieval

            if cached_data is not None:
                if not validation_function(cached_data):
                    if error_message:
                        raise ValueError(error_message)
                    else:
                        # Re-calculate the data if validation fails
                        cached_data = func(*args, **kwargs)
                        # Store the data in cache again
                        # (replace with your cache storage logic)
                        return cached_data
                else:
                    return cached_data # return cached value if validation is correct
            else:
                # Calculate the data if not in cache
                result = func(*args, **kwargs)
                # Store the data in cache (replace with your cache storage logic)
                return result
        return wrapper

    return decorator


if __name__ == "__main__":
    project_path = r"C:\Users\wired\OneDrive\Desktop\Projects\bm"  # Replace with your project folder path
    G = extract_py_code_graph(project_path)
    save=r"C:\Users\wired\OneDrive\Desktop\Projects\bm\data\extractors\project.json"
    # You can now use the graph for analysis or visualization
    # Example: Print nodes and edges
    asyncio.run(asave_data_checkpoint(path=save, content=nx.node_link_data(G)))
    for node_id, node_data in G.nodes(data=True):
        print(f"Node: {node_id}, Type: {node_data['type']}, Label: {node_data['label']}")
    for u, v, edge_data in G.edges(data=True):
        print(f"Edge: {u} -> {v}, Type: {edge_data['type']}")