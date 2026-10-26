import os
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


def inject_line_after_condition(
    base_dir: str | Path,
    match_groups: Iterable[Iterable[str]],
    injection_text: str = "    pass",
    file_extensions: set[str] | None = {".py"},
    excluded_dirs: set[str] = DEFAULT_EXCLUDED_DIRS,
    dry_run: bool = True,
) -> dict[Path, list[str]]:
    """Fügt unterhalb einer passenden Bedingung eine neue Zeile ein,

    JEDOCH NUR, wenn der Bereich unterhalb der Bedingung leer ist (kein
    eingerückter Code folgt).
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

            modified_lines = []
            injected_entries = []

            for i, line in enumerate(lines):
                modified_lines.append(line)

                # 1. Prüfen, ob die aktuelle Zeile die Match-Condition erfüllt
                is_match = any(
                    all(part in line for part in group) for group in groups
                )

                if is_match:
                    # 2. Prüfen, ob der nachfolgende Block bereits Inhalt hat
                    has_content_below = False
                    already_has_pass = False

                    # Iteriere durch die folgenden Zeilen, um den Körper der Klasse/Condition zu prüfen
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j]
                        stripped_next = next_line.strip()

                        # Ignoriere reine Leerzeilen bei der Prüfung
                        if not stripped_next:
                            continue

                        # Wenn die nächste Zeile mit Leerzeichen/Tab beginnt, gehört sie zum Block!
                        if next_line.startswith((" ", "\t")):
                            if stripped_next == injection_text.strip():
                                already_has_pass = True
                            else:
                                has_content_below = True
                            # Sobald wir den ersten Inhalt/Code im Block gefunden haben, abbrechen
                            break
                        else:
                            # Die nächste Zeile ist NICHT eingerückt (z.B. neue class/def/@decorator)
                            # -> Der Block ist somit LEER!
                            break

                    # 3. Injizieren NUR WENN kein Inhalt existiert UND noch kein pass da ist
                    if not has_content_below and not already_has_pass:
                        formatted_injection = (
                            injection_text
                            if injection_text.endswith("\n")
                            else f"{injection_text}\n"
                        )

                        modified_lines.append(formatted_injection)
                        injected_entries.append(
                            f"Injected 'pass' after line {i+1}: {line.strip()}"
                        )

            if not injected_entries:
                continue

            changes[path] = injected_entries

            if not dry_run:
                path.write_text(
                    "".join(modified_lines),
                    encoding="utf-8",
                )

    return changes


if __name__ == "__main__":
    root = Path(__file__).parent.parent.parent.resolve()
    print("Starte Injektion unter root:", root)

    modified_files = inject_line_after_condition(
        base_dir=root,
        match_groups=[
            ("class ", "ModelAdmin(BaseAdmin):"),
        ],
        injection_text="    pass",
        file_extensions={".py"},
        dry_run=False,
    )

    print(f"\nGeänderte Dateien ({len(modified_files)}):")
    for file_path, log in modified_files.items():
        print(f"\nFile: {file_path}")
        for entry in log:
            print(f"  -> {entry}")