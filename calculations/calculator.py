import ast
import pprint
import sympy as sp


class Calculator:
    def __init__(self, yaml_data, g):
        """
        Constructor for the Calculator class.

        Parameters:
        - yaml_data: The YAML content containing function definitions and parameters.
        - g: An external object (possibly a database or context) for retrieving values.
        """
        self.yaml_data = yaml_data
        self.g = g
        self.function_data = []
        print("Extracting functions and parameters from YAML data")
        self.extract_functions_from_yaml()

    def extract_functions_from_yaml(self):
        """
        Extracts function information from the provided YAML data, combining the
        parameter data from the three dictionaries (parent, child, edge_attrs).
        """
        for func in self.yaml_data:
            function_name = func["name"]
            description = func["description"]
            return_key = func["returns"]
            equation = func["equation"]
            params = func["parameters"]

            # Process parameters and default values
            param_dict = {}
            for param in params:
                param_name = param[0]
                param_type = param[1]
                param_default = param[2] if len(param) > 2 else None
                param_dict[param_name] = {
                    "type": param_type,
                    "default": param_default
                }

            self.function_data.append({
                "def_name": function_name,
                "description": description,
                "equation": equation,
                "params": param_dict,
                "dest_key": return_key,
            })

        print("Functions and parameters extracted:")
        pprint.pp(self.function_data)

    def match_to_powerset(self, powerset):
        """
        Matches function parameters to a given powerset (list of sets of arguments).
        """
        matched_functions = []
        for item in self.function_data:
            param_set = set(item["params"].keys())
            for power_item in powerset:
                if param_set == set(power_item):
                    matched_functions.append(
                        (item, param_set)
                    )
        return matched_functions

    def extract_single_args(self, args, parent, child, edge_attrs, call_args=None):
        """
        Aligns parameters from three dictionaries: parent, child, and edge_attrs.
        """
        call_args = call_args or {}
        for arg in args:
            if arg in parent:
                call_args[arg] = parent[arg]
            elif arg in child:
                call_args[arg] = child[arg]
            elif arg in edge_attrs:
                call_args[arg] = edge_attrs[arg]

            if arg.endswith("1") or arg.endswith("2"):
                bare_key = arg[:-1]
                if bare_key in parent and bare_key in child:
                    call_args[f"{bare_key}1"] = parent[bare_key]
                    call_args[f"{bare_key}2"] = child[bare_key]
        return call_args

    def run(self, func_name, params):
        """
        Runs the extracted function with the given parameters.

        Parameters:
        - func_name: Name of the function to run.
        - params: Dictionary containing the parameters for the function.
        """
        # Find the function in the function data
        func_data = next((item for item in self.function_data if item["def_name"] == func_name), None)
        if not func_data:
            raise ValueError(f"Function {func_name} not found in the extracted data.")

        # Prepare the function and parameters
        equation = func_data["equation"]
        param_dict = func_data["params"]

        # Substitute the parameters in the equation
        substituted_equation = equation
        for param_name, param_value in params.items():
            param_type = param_dict[param_name]["type"]
            substituted_equation = substituted_equation.replace(param_name, str(param_value))

        # Compute the result using sympy for mathematical expressions
        result = sp.sympify(substituted_equation)

        return result


# Example usage:

yaml_data = [
    {
        "name": "Coulomb's Law",
        "description": "Calculate the electrostatic force between two point charges.",
        "returns": "electrostatic_force",
        "equation": "k_e * charge1 * charge2 / r**2",
        "parameters": [
            ["charge1", "float"],
            ["charge2", "float"],
            ["r_vec", "np.ndarray"]
        ]
    },
    {
        "name": "Newton's Second Law",
        "description": "Calculate the force vector given mass and acceleration.",
        "returns": "force_vector",
        "equation": "mass * acceleration",
        "parameters": [
            ["mass", "float"],
            ["acceleration", "np.ndarray"]
        ]
    }
]

# Create a Calculator instance with YAML data and some external context `g`
calc = Calculator(yaml_data, g=None)

# Example of running a function (Coulomb's Law) with parameters
params = {
    "charge1": 1.0e-6,  # C
    "charge2": 2.0e-6,  # C
    "r_vec": [0.1, 0.2, 0.3]  # meters (just for example)
}

result = calc.run("Coulomb's Law", params)
print(f"Result: {result}")
