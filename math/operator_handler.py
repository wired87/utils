"""
OperatorHandler: Parses a code string (e.g. lambda_H*psi), splits by param/operator,
creates OPERATOR and PARAM nodes and links them recursively (p -> o -> p).
"""
import re
from typing import List
import ast

import networkx as nx
import numpy as np

from utils.graph.local_graph_utils import GUtils
from utils.math.operators import OPS

# Operators to split on (order matters for regex)
_OPS = r"([+\-*/])"


def split_eq(code: str) -> List[str]:
    """Split code into [param, op, param, op, ...]. Params are identifiers."""
    tokens = re.split(_OPS, code)
    return [t.strip() for t in tokens if t.strip()]


class OperatorHandler:
    """
    Receives GUtils, processes a code string, creates equation map (p -> o -> p).
    Set pathway -> for each eq
    Sepparate in Dublets first param represents the starting point for
    the equation pathway.
    a -> * -> b -> * -> c -> ...
    """

    def __init__(self, len_modules, methods):
        self.g = GUtils(G=nx.MultiDiGraph())
        self._op_counter = 0
        self.start_point_ctlr = [[] for _ in range(len_modules)]
        len_ops = len(list(OPS.keys()))
        self.ops_ctlr = np.arange(len_ops).tolist()
        self.ops_struct = [
            []
            for _ in range(len_ops)
        ]

        self.method_schema = None

        self.operator_pathway_ctlr = [[] for _ in range(len_modules)]

        self.grid_ctlr = []
        self.op_ctlr = []


    def add_ops(self):
        print("add op nodes...")
        for i, (k, v) in enumerate(OPS.items()):
            self.g.add_node({
                "nid": k,
                "type": "OPERATOR",
                "operator_idx": i,
            })
        print("add op nodes... done")


    def set_start_coords(self, midx, param_db_coords):
        for item in param_db_coords:
            self.start_point_ctlr[midx].append(item)
        return












def eq_extractor_main(equation, eq_store_item):
    """
    First indice in each item points to dest struct
    """
    print("eq_extractor_main...")
    # deriovate
    eq_idx_map = []

    eq_extractor = EqExtractor()

    eq_extractor.visit(
        ast.parse(equation, mode='eval')
    )

    for b in eq_extractor.batches:
        right_val = b['right']

        # add calculator function indices to method
        if right_val is None:
            # -
            left_val = b['left']
            fun_idx = list(OPS.keys()).index("neg")
            param_val = eq_store_item.index(left_val)

            # neg fun idx
            eq_idx_map.append([0, fun_idx])

            # param idx
            eq_idx_map.append([1, param_val])
        else:
            # +
            left_val = b['left']
            left_val_idx = eq_store_item.index(left_val)

            right_val = b['right']
            right_val_idx = eq_store_item.index(right_val)

            _operator = b['op']
            fun_idx = list(OPS.keys()).index(_operator)

            # left
            eq_idx_map.append([1, left_val_idx])

            # op fun idx
            eq_idx_map.append([0, fun_idx])

            # right
            eq_idx_map.append([1, right_val_idx])
    print("eq_extractor_main... done")
    return eq_idx_map


import ast


class EqExtractor(ast.NodeVisitor):
    def __init__(self):
        self.batches = []
        self.temp_count = 0

    def _get_target(self):
        target = f"temp_{self.temp_count}"
        self.temp_count += 1
        return target

    def visit_Call(self, node):
        # 1. Funktionsname extrahieren
        if isinstance(node.func, ast.Attribute):
            # Fall: psi.conj() -> op: 'conj', left: psi
            func_name = node.func.attr
            left_val = self.visit(node.func.value)
        elif isinstance(node.func, ast.Name):
            # Fall: jnp.dot(a, b) -> op: 'dot'
            func_name = node.func.id
            left_val = None
        else:
            func_name = "unknown_func"
            left_val = None

        args = [self.visit(arg) for arg in node.args]
        target = self._get_target()

        # Wenn es ein Methodenaufruf wie .conj() war, ist left_val gesetzt
        actual_left = left_val if left_val is not None else (args[0] if args else None)
        actual_right = args[1] if left_val is None and len(args) > 1 else (args[0] if left_val and args else None)

        self.batches.append({
            "left": actual_left,
            "op": func_name,
            "right": actual_right,
            "res": target,
            "all_args": args
        })
        return target

    def visit_Attribute(self, node):
        # Behandelt .T (Transponieren)
        value = self.visit(node.value)
        target = self._get_target()

        self.batches.append({
            "left": value,
            "op": node.attr,  # z.B. "T"
            "right": None,
            "res": target
        })
        return target

    def visit_Subscript(self, node):
        # Behandelt gamma[0]
        value = self.visit(node.value)
        # In Python 3.9+ ist node.slice direkt ein Constant oder Name
        index = self.visit(node.slice) if hasattr(node, 'slice') else "unknown_idx"

        target = self._get_target()
        self.batches.append({
            "left": value,
            "op": "get_item",
            "right": index,
            "res": target
        })
        return target

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_sym = self._get_op_sym(node.op)
        target = self._get_target()
        self.batches.append({"left": left, "op": op_sym, "right": right, "res": target})
        return target

    def _get_op_sym(self, op):
        mapping = {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*",
            ast.Div: "/", ast.MatMult: "@",
            ast.Pow: "**", ast.BitXor: "**"
        }
        return mapping.get(type(op), "unknown")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            target = self._get_target()
            self.batches.append({"left": operand, "op": "neg", "right": None, "res": target})
            return target

    def visit_Name(self, node):
        return node.id

    def visit_Constant(self, node):
        return node.value



if __name__ == "__main__":
    # Test-Gleichungen
    test_codes = [
        "a + jnp.dot(b, c)",  # Einfaches P-O-P
        "-a * b.conj().T",  # Negativer Parameter
        "(a + b) * (c - d)",  # Klammern und mehrere Batches
        "-x * (y + 5) / z^2"  # Komplexer Ausdruck (Hinweis: Python nutzt ** für Potenz)
    ]

    # Da Python's AST standardmäßig ** für Potenzen nutzt,
    # ersetzen wir ^ durch ** für den Parser.
    print(f"{'GLEICHUNG':<25} | {'BATCH-SCHRITTE (P-O-P)'}")
    print("-" * 80)

    for code in test_codes:
        print(f"{code:<25} | ", end="")
        try:
            # Wir bereiten den String kurz vor (Python-konforme Operatoren)
            clean_code = code.replace("^", "**")

            # Extraktion starten
            extractor = EqExtractor()
            extractor.visit(ast.parse(clean_code, mode='eval'))

            if not extractor.batches:
                print("Keine Operationen gefunden.")
                continue

            # Formatierte Ausgabe der Batches
            steps = []
            for b in extractor.batches:
                right_val = b['right'] if b['right'] is not None else ""
                steps.append(f"[{b['left']} {b['op']} {right_val} -> {b['res']}]")
            print("STEPS")
            print("  ".join(steps))
        except SyntaxError:
            print(f"Syntax Fehler in der Gleichung!")
        except Exception as e:
            print(f"Fehler: {e}")



"""


import ast

class EqExtractor(ast.NodeVisitor):
    def __init__(self):
        self.batches = []
        self.temp_count = 0

    def visit_Call(self, node):
        # 1. Funktionsnamen extrahieren (z.B. 'dot' aus 'jnp.dot')
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        else:
            func_name = "unknown_func"

        # 2. Argumente rekursiv auflösen
        # Das ist wichtig, falls in der Funktion wieder Rechnungen stehen!
        args = [self.visit(arg) for arg in node.args]

        target = f"temp_{self.temp_count}"
        self.temp_count += 1

        # Wir mappen Funktionen auf das P-O-P Schema
        # left = 1. Argument, right = 2. Argument (falls vorhanden)
        self.batches.append({
            "left": args[0] if len(args) > 0 else None,
            "op": func_name,
            "right": args[1] if len(args) > 1 else None,
            "res": target,
            "all_args": args # Für Funktionen mit > 2 Parametern
        })
        return target

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_sym = self._get_op_sym(node.op)
        target = f"temp_{self.temp_count}"
        self.temp_count += 1
        self.batches.append({"left": left, "op": op_sym, "right": right, "res": target})
        return target

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            target = f"temp_{self.temp_count}"
            self.temp_count += 1
            self.batches.append({"left": operand, "op": "neg", "right": None, "res": target})
            return target

    def visit_Name(self, node):
        return node.id

    def visit_Constant(self, node):
        return node.value

    def _get_op_sym(self, op):
        if isinstance(op, ast.Add): return "+"
        if isinstance(op, ast.Sub): return "-"
        if isinstance(op, ast.Mult): return "*"
        if isinstance(op, ast.Div): return "/"
        if isinstance(op, (ast.Pow, ast.BitXor)): return "**"
        return "unknown"





"""