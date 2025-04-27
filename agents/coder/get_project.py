import os
import ast

from utils.agents.coder.py.main import CodeGraphUploader
from utils.utils import GraphUtils


class ProjectExtractor:
    def __init__(self, g):
        self.root_path = r"C:\Users\wired\OneDrive\Desktop\Projects\bm\_betse"
        self.project_structure = {}
        self.ignore = []

        self.g_utils = g

    def extract_code_and_imports(self, file_path):
        """
        Opens a Python file, extracts its full code content, and identifies all imported
        modules and objects.

        Args:
            file_path (str): The path to the Python file.

        Returns:
            tuple: A tuple containing:
                - str: The entire code content of the file.
                - list: A list of unique names of imported modules/objects.
                Returns (None, None) if the file cannot be read or parsed.
        Raises:
            FileNotFoundError: If the file_path does not exist.
            SyntaxError: If the file contains invalid Python syntax.
            Exception: For other potential file reading errors.
        """

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: File not found at {file_path}")
        file_name = file_path.split("/")[-1].split("\\")[-1]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_code = f.read()


        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            raise  # Re-raise the exception after printing





        imports_set = set()

        try:
            tree = ast.parse(full_code, filename=file_path)

            for node in ast.walk(tree):

                if isinstance(node, ast.Import):
                    self.g_utils.add_edge(
                        file_name,
                        node,
                        attrs=dict(type="BETSE13",
                                   rel="import_content",
                                   src_layer="file",
                                   trgt_layer="file")
                    )

                    # Handles 'import module' or 'import module as alias'
                    for alias in node.names:
                        imports_set.add(alias.name)  # Add the original module name
                elif isinstance(node, ast.ImportFrom):
                    self.g_utils.add_edge(
                        file_name,
                        file_path,
                        attrs=dict(type="BETSE13", rel="import_origin",
                                   src_layer="file",
                                   trgt_layer="file")
                    )

                    if node.module:
                        # Optionally add the base module/package from which things are imported
                        # imports_set.add(node.module) # Uncomment if you want 'os' in addition to 'path' from 'from os import path'
                        pass  # Often, users just want the specific things imported

                    for alias in node.names:
                        # alias.name is the specific module/object imported (e.g., 'path')
                        # Construct the full path if importing a submodule/object
                        full_import_name = f"{node.module}.{alias.name}" if node.module else alias.name
                        # However, the request asks for original files/libs,
                        # 'alias.name' usually represents the most direct item imported
                        imports_set.add(alias.name)  # Add the specific imported name ('path')
                if isinstance(node, ast.Module):
                    #print("Add_node", node,  "file_n<me", file_name, full_code)
                    self.g_utils.add_node(

                        attrs=dict(
                            id=file_path,
                            code=full_code,
                            type="BETSE13",
                        )
                    )
        except SyntaxError as e:
            print(f"Error parsing Python code in {file_path}: {e}")
            raise  # Re-raise the syntax error
        except Exception as e:
            print(f"An unexpected error occurred during AST processing: {e}")
            raise  # Re-raise other potential AST errors


    def extract(self):
        print("start")
        current_parent = None
        for root, _, files in os.walk(self.root_path):
            # if current_parent is not None:
            # self.g_utils.G.add_node(current_parent)
            if len(files) > 200:
                print(f"Too many files in {root}, skipping")
                continue
            for file in files:
                current_path = os.path.join(root, file)
                if current_path in self.ignore:
                    print("Path excluded")
                    continue


                if file.endswith('.py'):
                    #self.project_structure[file] = self._parse_file(current_path)
                    self.extract_code_and_imports(current_path)

        #pprint.pp(self.get_project_structure())
        print("Finished")
        return self.g_utils.G

    def _parse_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                tree = ast.parse(content)
            except Exception:
                return

        file_info = {
            "type": "file",
            "libs": [],
            "content": {
                "classes": {},
                "functions": {},
                "variables": [],
                "comments": []
            }
        }

        imports = []
        variables = []
        # comments = self._extract_comments(content)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(self._parse_import(node))
            elif isinstance(node, ast.ClassDef):
                file_info["content"]["classes"][node.name] = self._parse_class(node, content)
            elif isinstance(node, ast.FunctionDef):
                file_info["content"]["functions"][node.name] = self._parse_function(node, content)
            elif isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                variables.extend(targets)

        file_info["libs"] = imports
        file_info["content"]["variables"] = variables
        # file_info["content"]["comments"] = comments
        return file_info

    def _parse_import(self, node):
        if isinstance(node, ast.Import):
            return [alias.name for alias in node.names][0]
        elif isinstance(node, ast.ImportFrom):
            return node.module
        return None

    def _parse_class(self, node, content):
        class_info = {
            "methods": {},
            "variables": []
        }
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_info["methods"][item.name] = self._parse_function(item, content)
            elif isinstance(item, ast.Assign):
                targets = [t.id for t in item.targets if isinstance(t, ast.Name)]
                class_info["variables"].extend(targets)
        return class_info

    def _parse_function(self, node, content):
        decorators = [ast.unparse(deco) for deco in node.decorator_list]
        variables = []
        for inner_node in ast.walk(node):
            if isinstance(inner_node, ast.Assign):
                targets = [t.id for t in inner_node.targets if isinstance(t, ast.Name)]
                variables.extend(targets)
        # Extract the actual function code
        func_code = ast.get_source_segment(content, node)
        return {
            "decorators": decorators,
            "variables": variables,
            "comments": [],
            "code": func_code  # <---- Full function code here
        }

    def _extract_comments(self, content):
        comments = []
        inside_multiline = False
        multiline_delim = None
        buffer = []

        for line in content.splitlines():
            stripped = line.strip()

            if inside_multiline:
                buffer.append(stripped)
                if stripped.endswith(multiline_delim):
                    comments.append("\n".join(buffer))
                    inside_multiline = False
                    buffer = []
                continue

            if any(stripped.startswith(start) for start in ("#", "'''", '"""', "r'''", 'r"""', "rf'''", 'rf"""')):
                if stripped.startswith("#"):
                    comments.append(stripped)
                else:
                    if (stripped.endswith("'''") or stripped.endswith('"""')) and len(stripped) > 6:
                        comments.append(stripped)
                    else:
                        inside_multiline = True
                        if "'''" in stripped:
                            multiline_delim = "'''"
                        else:
                            multiline_delim = '"""'
                        buffer.append(stripped)
        return comments

    def get_project_structure(self):
        return self.project_structure


if __name__ == '__main__':
    g = GraphUtils(upload_to="sp", table_name="BETSE13")

    extractor = ProjectExtractor(g)
    extractor.extract()
    pyg_creator = CodeGraphUploader(g)
    pyg_creator.upload()
