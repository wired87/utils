import numpy as np
import sympy as sp



class Calculator:
    def __init__(self, g, calculations:list):
        self.g = g
        self.calculations = calculations

    def main(self, parent, child, edge_attrs, env_attrs):
        print("Start calc process")

        sources = {
            "parent":parent,
            "child": child,
            "edge_attrs":edge_attrs,
            "env_attrs":env_attrs
        }


        # Get function
        for calc_item in self.calculations:
            result, key = self._calc(
                calc_item,
                sources
            )
            if result is not None:
                if key in parent:
                    parent[key] = result

                elif key in edge_attrs:
                    parent[key] = result

                elif key in env_attrs:
                    parent[key] = result

        print("Finished calc process")
        return parent

    def _calc(
            self,
            calc_item,
            sources:dict,
    ):

        function_name = calc_item["name"]
        returns = calc_item["returns"]
        equation = calc_item["equation"]
        params = calc_item["parameters"]

        # Get Values for params
        extracted_params, value_dict_dest = self._extract_single_args(
            params,
            sources,
        )

        # Calc
        result = self._run(equation, eq_args=extracted_params)

        print(f"{function_name} calc result:", result)
        return result, returns

    def _resolve_arg(self, arg, sources):
        for calc_item in self.calculations:
            if calc_item["returns"] == arg:
                result = self._calc(
                    calc_item,
                    sources
                )
                return result
    def _validate_value(self, key, sources, current_loop_object, name):
        """
        Case: val1, val2 required
        Get value from correct dict based on
        """
        if key[:-1].isdigit():
            if int(key) == int("1"):
                return sources["parent"][name]
            elif int(key) == int("2"):
                return sources["child"][name]
        return current_loop_object[name]





    def _extract_single_args(self, required_args, sources:dict):
        """
        Tries to collect all arguments required for an equation from provided sources.
        If a value is not found directly or via default, it attempts to resolve it through another calculation.
        """
        collected_args = {}
        value_dict_dest = None

        for item in required_args:
            name, last_char = self._validate_arg(item["name"])
            found = False

            # Add key to in collection
            key = f"{name}{last_char}" if last_char is not None else name

            # Check all input sources (parent, child, edge_attrs, env_attrs)
            for origin, object_value in sources.items():
                if name in object_value:
                    value = self._validate_value(
                        key,
                        sources,
                        object_value,
                        name
                    )
                    print("name, value, required_args", name, value, item)
                    collected_args[key] = self._convert_type(value, item)
                    print(f"[FOUND] {name} in input sources: {value}")
                    found = True
                    break

            # Check for default value
            if not found:
                default = item.get("default_value", None)
                if default is not None:
                    print("name, value, required_args", name, default, item)
                    collected_args[key] = self._convert_type(default, item)
                    print(f"[DEFAULT] Used default for {name}: {default}")
                    found = True

            # Try to calculate missing argument via known equations
            if not found:
                print(f"[MISSING] {key} not found in sources or defaults. Attempting to calculate...")
                result = self._resolve_arg(name, sources)
                if result is None:
                    print(f"[FAIL] Could not resolve {name}. Aborting argument extraction.")
                    return None, None
                collected_args[key] = result
                print(f"[CALCULATED] {name} was computed as: {result}")

        return collected_args, value_dict_dest



    def _validate_arg(self, arg):
        last_char = arg[-1]
        if last_char.isdigit():  # endswith 1,2,3,...
            base = arg[:-1]
            return base, last_char
        return arg, None

    def _convert_type(self, value, item):
        param_type = item["type"]
        if param_type == "float":
            return float(value)
        elif param_type == "np.ndarray":
            return np.array(value, dtype=float)
        elif param_type == "int":
            return int(value)
        elif param_type == "dict":
            return dict(value)
        elif param_type == "np.log":
            print("np.log param type value", value)
            return np.log(float(value))
        else:
            return value


    def _run(self, equation, eq_args):
        try:
            result = eval(equation, {"np": np, "sp": sp, **eq_args})
            return result
        except Exception as e:
            print(f"Error running equation: {e}")
            return None


"""


    def _extract_single_args2(self, required_args, sources):
        collected_args = {}
        value_dict_dest=None
        for item in required_args:
            name = item["name"]
            found = False
            for source in sources:
                if name in source:
                    value = source[name]
                    collected_args[name] = self._convert_type(name, value, required_args)
                    found = True
                    break

            if not found:
                default = required_args[name].get("default", None)
                if default is not None:
                    collected_args[name] = self._convert_type(name, default, required_args)
                else:
                    # Required args could not be collected
                    # from given dicts ->
                    # try calc missing values from
                    # equations
                    result = self._resolve_arg(
                        name,
                        sources
                    )
                    if result is None:
                        return None
                    collected_args[name] = result

        return collected_args, value_dict_dest

"""