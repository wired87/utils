import os
import ast
from utils.gnn.embedder import embed
from utils.utils import GraphUtils


class ProjectExtractor:
    def __init__(self, g:GraphUtils):
        
        self.local_modules = None
        self.repo_id = None
        self.root_path = None
        self.requirements = []
        self.project_structure = {}
        self.ignore = []

        self.g = g



    def extract(self, root, repo_id, repo_name):
        print("start extraction")

        self.root_path = root
        print("Project root", root)

        self.repo_id = repo_id
        print("repo_id", repo_id)

        self.repo_name = repo_name

        self.local_modules = [os.path.basename(root) for root, _, _ in os.walk(self.root_path)]

        readme = self.extract_metadata()
        # Create a node for the repo
        self.g.add_node(
            attrs=dict(
                id=self.repo_id,
                type="REPO",
                readme=embed(readme) if readme is not None else embed("default"),
                requirements=self.requirements
            )
        )

        for root, _, files in os.walk(self.root_path):
            for file in files:
                current_path = os.path.join(root, file)
                if current_path in self.ignore:
                    print("Path excluded")
                    continue

                if file.endswith('.py'):
                    # self.project_structure[file] = self._parse_file(current_path)
                    file_name, full_code = self.handle_file_content(current_path)

                    file_id = self.handle_code(file_name, full_code, current_path)

                    self.handle_imports(
                        full_code,
                        file_id,
                        file_path=current_path
                    )

        print("Finished")

    def handle_code(self, file_name, full_code, current_path):
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
        #print("current_path", current_path)
        print("current_path", current_path)
        current_path_proj_root = current_path.replace(self.root_path, "")
        print("current_path_proj_root", current_path_proj_root)

        file_id = current_path_proj_root.replace("\\", ".").replace("/", ".")

        if file_id.startswith("."):
            file_id = file_id[1:]
        print("Add file", file_id)

        self.g.add_node(
            attrs=dict(
                id=file_id,
                type="FILE",
                embed=embed(full_code),
                code=full_code
            )
        )
        self.g.add_edge(
            src=self.repo_id,
            trt=file_id,
            attrs=dict(
                src_layer="REPO",
                trgt_layer="FILE",
                rel="has"
            )
        )
        return file_id


    def extract_code(self, node, lines):
        """Extract code from ast node"""
        start = node.lineno - 1
        end = node.end_lineno  # includes end line
        return "\n".join(lines[start:end])

    def extract_comments(
            self,
            full_code,

    ):
        file_comments=[]
        # Extract comments
        for i, line in enumerate(full_code.splitlines(), start=1):
            if line.startswith("#"):
                file_comments.append((i, line.strip()))
            if line.startswith(('"""', "'''",)):
                start_line = i
                end_line = None
                for end_index, line in enumerate(full_code.splitlines()[start_line:], start=start_line):
                    if line.strip.endswith(('"""', "'''",)):
                        end_line = end_index

                full_comment = "\n".join(full_code[start_line:end_line])
                file_comments.append(full_comment)
        return file_comments


    def handle_file_content(self, file_path):
        file_name = file_path.split("/")[-1].split("\\")[-1]
        with open(file_path, 'r', encoding='utf-8') as f:
            full_code = f.read()
        return file_name, full_code




    def is_local_import(self, module_name):
        if "." in module_name:
            module_name = module_name.split(".")[0]

        if module_name in self.local_modules and module_name not in self.requirements:
            print("Local Module:", module_name)
            return True
        else:
            print("Lib import", module_name)
        return False

    def handle_imports(self, full_code, file_id, file_path):
        tree = ast.parse(full_code, filename=file_path)
        #variables = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name  # Use alias.name inside ast.Import
                    print("Module name", module_name)
                    self.g.add_edge(
                        file_id,
                        module_name,
                        attrs=dict(
                            rel="import",
                            src_layer="FILE",
                            trgt_layer="LIB" if not self.is_local_import(module_name) else "LOCAL"
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""  # might be None
                for alias in node.names:
                    imported_name = alias.name
                    self.g.add_edge(
                        file_id,
                        f"{module_name}.{imported_name}",
                        attrs=dict(
                            rel="import_from",
                            src_layer="FILE",
                            trgt_layer="LIB" if not self.is_local_import(module_name) else "LOCAL"
                        )
                    )




    def extract_metadata(self):
        readme=None
        for root, _, files in os.walk(self.root_path):
            for file in files:
                current_path = os.path.join(root, file)
                if current_path in self.ignore:
                    print("Path excluded")
                    continue

                if file == 'README.md':
                    readme = open(current_path, "r", encoding="utf-8").read()
                elif file.startswith("requirements"):
                    requirements=[]
                    requirements_file = open(current_path, "r", encoding="utf-8").read()
                    for line in requirements_file.splitlines():
                        stripped = line.strip()
                        if len(stripped):
                            if not stripped.startswith("#") and stripped[-1].isdigit():
                                self.requirements.append(stripped)
        print("Project Metadata Extracted")
        return readme

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




"""try:
    tree = ast.parse(full_code, filename=file_path)
    variables = []

    file_comments:list = self.extract_comments(
        full_code
    )
    self.g.add_node(
        attrs=dict(
            id=f"{file_name}_file_comment_{len(file_comments)}",
            code=full_code,
            type="COMMENT",
        )
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            self.g.add_node(
                attrs=dict(
                    id=f"{file_name}_{node.name}",
                    code=full_code,
                    type="CLASS",
                )
            )



        # DEF
        elif isinstance(node, ast.FunctionDef):
            self.g.add_node(
                attrs=dict(
                    id=f"{file_name}_{node.name}",
                    code=full_code,
                    type="DEF",
                )
            )

        # VARIABLES
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    val = ast.literal_eval(node.value) if isinstance(node.value, (
                    ast.Constant, ast.Num, ast.Str, ast.List, ast.Dict, ast.Tuple)) else "complex_expr"
                    variables.append((target.id, val))






except SyntaxError as e:
    print(f"Error parsing Python code in {file_path}: {e}")
    raise  # Re-raise the syntax error
except Exception as e:
    print(f"An unexpected error occurred during AST processing: {e}")
    raise  # Re-raise other potential AST errors"""