import ast
import pprint


class Calculator:
    def __init__(self, code_str: str, g):
        self.code_str = code_str
        self.function_data=[]
        self.g=g
        print("Extracting functions with params")
        self.extract()

    def extract(self):
        """
        Extracts all functions, their arguments, and return key (from `returns = "..."`)
        and compiles the function as a callable object.
        """
        # Request Equations from BQ
        """query = self.g.select_all_from_table_query()
        equations:list = self.g.run_query(query, conv_to_dict=True)
        for eq in equations:

            expr = parse_expr(eq["equation"])
            eq_args = expr.free_symbols
            self.function_data.append({
                "def_name": eq["name"],
                "description": eq["description"],
                "args": eq_args,
                "dest_key": eq["dest_key"],
            })"""

        tree = ast.parse(self.code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args]
                func_code = ast.unparse(node)

                # Compile the function so it's callable
                local_scope = {}
                exec(func_code, {}, local_scope)
                func_obj = local_scope[node.name]

                # Extract return variable name (if set via `returns = "..."`)
                return_var = None
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id == "returns":
                                if isinstance(stmt.value, ast.Constant):
                                    return_var = stmt.value.value

                self.function_data.append({
                    "def_name": node.name,
                    "runnable": func_obj,  # ✅ now a real Python function
                    "args": params,
                    "dest_key": return_var,
                })
        print("Funciton data extracted")
        pprint.pp(self.function_data)
        return self.function_data

    def match_to_powerset(self, powerset) -> list:
        matched_functions = []
        for item in self.function_data:
            param_set = set(item["args"])
            for power_item in powerset:
                if param_set == set(power_item):
                    matched_functions.append(
                        (
                            item,
                            param_set
                        )
                    )
        return matched_functions


    def match_to_function_keys(self, f1, f2):

        for item in self.function_data:
            calc_values = {}
            for k, v in f2.items():
                for arg in item["args"]:
                    if arg == k and k not in calc_values: # check same & avoid overwriting
                        calc_values[k] = v

            if len(calc_values.values()) == len(item["args"]): # all values present todo amke better
                pass



