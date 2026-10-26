from __future__ import annotations

import os
import shutil
from pathlib import Path


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "media",
    "node_modules",
    "staticfiles",
    "venv",
}


def delete_named_directories(
    base_dir: str | Path,
    directory_name: str,
    excluded_dirs: set[str] | None = None,
    *,
    dry_run: bool = True,
) -> list[Path]:
    """
    Findet oder löscht alle Verzeichnisse mit dem exakten Namen.

    Ausgeschlossene Verzeichnisse werden nicht durchsucht.
    Symlinks werden nicht verfolgt oder gelöscht.
    """
    root = Path(base_dir).expanduser().resolve(strict=True)

    if not root.is_dir():
        raise NotADirectoryError(root)

    if (
        not directory_name
        or Path(directory_name).name != directory_name
    ):
        raise ValueError(
            "directory_name muss ein einfacher Verzeichnisname sein"
        )

    excluded = (
        DEFAULT_EXCLUDED_DIRS
        if excluded_dirs is None
        else excluded_dirs
    )

    matches: list[Path] = []

    for current_dir, dirnames, _ in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current_dir)
        remaining_dirs: list[str] = []

        for name in dirnames:
            path = current_path / name

            if name in excluded:
                continue

            if name == directory_name:
                if path.is_symlink() or not path.is_dir():
                    continue

                matches.append(path)

                if not dry_run:
                    shutil.rmtree(path)

                # Nicht mehr in das gefundene Verzeichnis hineinlaufen
                continue

            remaining_dirs.append(name)

        # Bestimmt, welche Verzeichnisse os.walk als Nächstes besucht
        dirnames[:] = remaining_dirs

    return matches


def main() -> None:
    base_dir = Path(__file__).resolve().parents[2]

    for directory_name in ["migrations"]:
        matches = delete_named_directories(
            base_dir=base_dir,
            directory_name=directory_name,
            excluded_dirs=DEFAULT_EXCLUDED_DIRS,
            dry_run=False,  # zuerst nur anzeigen
        )

        for path in matches:
            print(f"FOUND: {path}")

    print(f"{len(matches)} directories found")


if __name__ == "__main__":
    main()