import os
from pathlib import Path
from collections.abc import Iterable

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    "media",
    "staticfiles",
}



def prepend_statements_to_named_files(
    base_dir: str | Path,
    filename: str,
    statements: Iterable[str],
    excluded_dirs: set[str] | None = None,
    *,
    dry_run: bool = True,
) -> dict[Path, list[str]]:
    """
    Fügt Statements am Anfang aller Dateien mit dem exakten Namen ein.

    Bereits vorhandene Statements werden nicht erneut eingefügt.
    """
    root = Path(base_dir).expanduser().resolve(strict=True)

    if not root.is_dir():
        raise NotADirectoryError(root)

    if not filename or Path(filename).name != filename:
        raise ValueError(
            "filename muss ein einfacher Dateiname sein"
        )

    excluded = (
        DEFAULT_EXCLUDED_DIRS
        if excluded_dirs is None
        else excluded_dirs
    )

    normalized_statements = [
        statement.rstrip("\r\n")
        for statement in statements
        if statement.strip()
    ]

    changes: dict[Path, list[str]] = {}

    for current_dir, dirnames, filenames in os.walk(
        root,
        topdown=True,
    ):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in excluded
        ]

        if filename not in filenames:
            continue

        path = Path(current_dir, filename)

        if path.is_symlink() or not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        existing_lines = {
            line.strip()
            for line in content.splitlines()
        }

        missing_statements = [
            statement
            for statement in normalized_statements
            if statement.strip() not in existing_lines
        ]

        if not missing_statements:
            continue

        changes[path] = missing_statements

        if dry_run:
            continue

        prefix = "\n".join(missing_statements) + "\n"

        if content:
            prefix += "\n"

        path.write_text(
            prefix + content,
            encoding="utf-8",
        )

    return changes


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]

    changes = prepend_statements_to_named_files(
        base_dir=root,
        filename="models.py",
        statements=[
            "from oasismarket.abc.base_model_custom import BaseModel",
            "from oasismarket.utils.get_file_dir import get_file_dir",
        ],
        excluded_dirs=DEFAULT_EXCLUDED_DIRS | {
            "migrations",
        },
        dry_run=False,
    )

    for path, added_statements in changes.items():
        print(f"Geändert: {path}")

        for statement in added_statements:
            print(f"  APPEND: {statement}")

