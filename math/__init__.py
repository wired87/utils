import itertools
import operator
import os

import numpy as np

from utils.file.yaml import load_yaml

MGLOBALS= r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\math\globals.yaml" if os.name == "nt" else "utils/math/globals.yaml"
MGLOBALSC = load_yaml(MGLOBALS)




# WICHTIG FÜR MATH G ENGINE Alle relevanten Python-Operatoren als Funktionen
OPS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': lambda x, y: np.divide(x, y, where=y!=0),
    '**': operator.pow,
    '%': operator.mod,
    '//': lambda x, y: np.floor_divide(x, y, where=y!=0),
    '==': operator.eq,
    '!=': operator.ne,
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
    '&': operator.and_,
    '|': operator.or_,
    '^': operator.xor,
    '<<': operator.lshift,
    '>>': operator.rshift,
}

def apply_all_operator_combinations(variables):
    results = {}

    keys = list(variables.keys())
    combos = itertools.combinations(keys, 2)
    op_patterns = list(OPS.items())

    for (a, b) in combos:
        for symbol, func in op_patterns:
            name = f"{a}{symbol}{b}"
            try:
                res = func(variables[a], variables[b])
                results[name] = res
            except Exception as e:
                results[name] = f"Error: {e}"

    return results

# Beispiel: Matrix und Skalarwerte
r"""x = {
    'a': np.array([[1, 2], [3, 4]]),
    'b': np.array([[2, 0], [1, 2]]),
    'c': 5
}

results = apply_all_operator_combinations(x)

# Ausgabe (nur ein paar Ergebnisse)
for k, v in list(results.items())[:10]:
    print(f"{k}:\n{v}\n")
"""



