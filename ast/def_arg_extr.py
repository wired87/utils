import ast

class FunctionParameterExtractor:
    def __init__(self, code_str: str):
        self.code_str = code_str
        self.function_data=[]

        print("Extracting functions with params")
        self.extract()

    def extract(self):
        """
        Extracts all functions and args from given str
        :return: list[dict]
        """
        tree = ast.parse(self.code_str)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args]
                func_code = ast.unparse(node)
                self.function_data.append(
                    {
                        "def_name": node.name,
                        "runnable": func_code,
                        "args": params,
                    }
                )
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
        calc_values={}
        for k, v in f1.items():
            for item in self.function_data:
                for arg in item["args"]:
                    if arg == k:
                        calc_values[k] = v
        calc_values2={}
        for k, v in f2.items():
            for item in self.function_data:
                for arg in item["args"]:
                    if arg == k:
                        calc_values[k] = v

        if len()


