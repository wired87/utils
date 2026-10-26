import os
import pprint
from collections.abc import Iterable
from pathlib import Path

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


def _get_bracket_delta(line: str) -> int:
    """Zählt die Differenz zwischen öffnenden und schließenden Klammern in einer Zeile.

    Strings in Anführungszeichen werden ignoriert, um Klammern innerhalb von
    Strings nicht mitzuzählen.
    """
    delta = 0
    in_single_quote = False
    in_double_quote = False
    escaped = False

    for char in line:
        if escaped:
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue

        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            continue

        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            continue

        # Wenn wir uns nicht in einem String befinden, Klammern zählen
        if not in_single_quote and not in_double_quote:
            if char in "([{":
                delta += 1
            elif char in ")]}":
                delta -= 1

    return delta


def delete_matching_lines(
    base_dir: str | Path,
    match_groups: Iterable[Iterable[str]],
    file_extensions: set[str] | None = None,
    excluded_dirs: set[str] = DEFAULT_EXCLUDED_DIRS,
    dry_run: bool = True,
) -> dict[Path, list[str]]:
    """Entfernt passende Zeilen oder mehrzeilige Datenstrukturen (z. B.

    multiline list_display = (...)) aus allen Dateien unterhalb von base_dir.
    """
    root = Path(base_dir).expanduser().resolve(strict=True)

    excluded = (
        DEFAULT_EXCLUDED_DIRS if excluded_dirs is None else excluded_dirs
    )

    groups = [tuple(group) for group in match_groups]

    changes: dict[Path, list[str]] = {}

    for current_dir, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [name for name in dirnames if name not in excluded]

        for filename in filenames:
            path = Path(current_dir, filename)

            if path.is_symlink() or not path.is_file():
                continue

            if file_extensions and path.suffix not in file_extensions:
                continue

            try:
                lines = path.read_text(encoding="utf-8").splitlines(
                    keepends=True
                )
            except (UnicodeDecodeError, OSError):
                continue

            removed_lines = []
            remaining_lines = []

            skip_until_bracket_depth = 0
            is_deleting_multiline = False

            for line in lines:
                # 1. Wenn wir aktuell eine mehrzeilige Struktur löschen:
                if is_deleting_multiline:
                    removed_lines.append(line.rstrip("\r\n"))
                    skip_until_bracket_depth += _get_bracket_delta(line)

                    # Sobald alle klammern der Struktur geschlossen sind, stoppen
                    if skip_until_bracket_depth <= 0:
                        is_deleting_multiline = False
                        skip_until_bracket_depth = 0
                    continue

                # 2. Prüfen, ob die aktuelle Zeile ein Match ist
                should_delete = any(
                    all(part in line for part in group) for group in groups
                )

                if should_delete:
                    removed_lines.append(line.rstrip("\r\n"))
                    bracket_delta = _get_bracket_delta(line)

                    # Falls mehr Klammern geöffnet als geschlossen wurden -> Mehrzeilige Struktur!
                    if bracket_delta > 0:
                        is_deleting_multiline = True
                        skip_until_bracket_depth = bracket_delta
                else:
                    remaining_lines.append(line)

            if not removed_lines:
                continue

            changes[path] = removed_lines

            if not dry_run:
                path.write_text(
                    "".join(remaining_lines),
                    encoding="utf-8",
                )

    pprint.pp(changes)
    return changes


if __name__ == "__main__":
    root = Path(__file__).parent.parent.parent.resolve()
    print("root", root)
    delete_matching_lines(
        base_dir=root,
        match_groups=[
            ["list_display ="],
        ],
        dry_run=True,
    )