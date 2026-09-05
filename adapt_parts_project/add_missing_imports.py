import ast
from pathlib import Path

from firegraph.graph import GUtils
from firegraph.graph_creator import StructInspector


def fix_missing_imports(
    base_dir: str | Path,
    dry_run: bool = True,
) -> dict[Path, list[str]]:
    """Nutzt StructInspector & GUtils, um unvollständige Imports im Projekt zu erkennen

    und fehlende Absolute-Import-Statements an den Anfang der betroffenen Dateien zu schreiben.
    """
    root = Path(base_dir).expanduser().resolve(strict=True)

    # 1. Graph und Inspector initialisieren
    graph = GUtils()
    inspector = StructInspector(g=graph, _log=False)
    inspector.drf = None  # Schwere DRF-Extensions deaktivieren

    # 2. Bestehende Logik von StructInspector nutzen: Durchsucht base_dir, baut den Graphen & verlinkt Imports
    inspector.convert_module_to_graph(base_dir=root)

    # Map aufbauen: Welche Datei gehört zu welchem Modulpfad?
    module_path_to_filepath: dict[str, Path] = {}
    exported_symbols: dict[str, str] = {}

    for nid, attrs in graph.G.nodes(data=True):
        ntype = attrs.get("type", "")

        if ntype == "MODULE":
            file_p = attrs.get("path")
            if file_p:
                module_path_to_filepath[nid] = Path(file_p)

        # 3. Exportierte Symbole (Klassen, Views, Models, Admin etc.) aus dem Graphen auslesen
        module_path = attrs.get("module") or attrs.get("module_id")
        if ntype.endswith("_CLASS") or ntype == "CLASS":
            symbol_name = attrs.get("name") or nid.split(".")[-1]
            if module_path:
                exported_symbols[symbol_name] = module_path
        elif ntype == "METHOD" and module_path:
            symbol_name = nid.split(".")[-1]
            if not symbol_name.startswith("_"):
                exported_symbols[symbol_name] = module_path

    changes: dict[Path, list[str]] = {}

    for module_path, filepath in module_path_to_filepath.items():
        if not filepath.is_file() or filepath.suffix != ".py":
            continue

        try:
            code_content = filepath.read_text(encoding="utf-8-sig")
            tree = ast.parse(code_content)
        except Exception:
            continue

        existing_imported_names: set[str] = set()
        defined_local_names: set[str] = set()
        referenced_names: set[str] = set()

        # AST-Analyse für lokale/importierte vs. genutzte Namen
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    existing_imported_names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    existing_imported_names.add(alias.asname or alias.name)
            elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_local_names.add(node.name)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    defined_local_names.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    referenced_names.add(node.id)

        # Fehlende Imports ermitteln
        missing_statements: list[str] = []
        for symbol in referenced_names:
            if symbol in defined_local_names or symbol in existing_imported_names:
                continue

            target_module = exported_symbols.get(symbol)
            if target_module and target_module != module_path:
                stmt = f"from {target_module} import {symbol}"
                if stmt not in missing_statements:
                    missing_statements.append(stmt)

        if not missing_statements:
            continue

        changes[filepath] = missing_statements

        # 5. Injektion in die erste Zeile der Datei
        if not dry_run:
            lines = code_content.splitlines(keepends=True)
            insert_idx = 0
            if lines and (lines[0].startswith("#!") or "coding" in lines[0]):
                insert_idx = 1

            new_import_block = "\n".join(missing_statements) + "\n"
            lines.insert(insert_idx, new_import_block)
            filepath.write_text("".join(lines), encoding="utf-8")
    return changes


if __name__ == "__main__":
    changes = fix_missing_imports(
        base_dir=Path(__file__).resolve().parent.parent,
        dry_run=True,
    )
    import pprint
    pprint.pp(changes)