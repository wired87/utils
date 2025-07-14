from pathlib import Path


def convert_path_any_os(relative_path: str):
    # Pfad auflösen relativ zum aktuellen Skript (nicht cwd!)
    base = Path(__file__).parent
    path = (base / relative_path).resolve()
    return path