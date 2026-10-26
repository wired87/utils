from __future__ import annotations

import os
import shutil
from collections.abc import Iterable
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


def _validate_folder_names(folder_names: Iterable[str]) -> set[str]:
    validated: set[str] = set()
    for folder_name in folder_names:
        if (
            not isinstance(folder_name, str)
            or not folder_name
            or Path(folder_name).name != folder_name
            or folder_name in {".", ".."}
        ):
            raise ValueError(
                "Each del_folder item must be a simple folder name without a path."
            )
        validated.add(folder_name)
    return validated


def delete_folders(
    base_dir: str | Path,
    del_folder: Iterable[str],
    excluded_dirs: set[str] | None = None,
    *,
    dry_run: bool = True,
) -> list[Path]:
    """
    Find or delete_user every directory whose name occurs in ``del_folder``.

    Traversal never enters excluded directories, never follows symlinks, and
    never deletes the resolved project root itself. ``dry_run`` defaults to
    True so callers can inspect the exact targets before deletion.

    Example::

        matches = delete_folders(
            base_dir=project_root,
            del_folder=["migrations"],
            dry_run=True,
        )
    """
    root = Path(base_dir).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(root)

    targets = _validate_folder_names(del_folder)
    if not targets:
        return []

    excluded = set(DEFAULT_EXCLUDED_DIRS if excluded_dirs is None else excluded_dirs)
    conflicts = targets.intersection(excluded)
    if conflicts:
        names = ", ".join(sorted(conflicts))
        raise ValueError(
            f"Target folders are also excluded and cannot be reached: {names}"
        )

    matches: list[Path] = []
    for current_dir, dirnames, _filenames in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current_dir)
        remaining_dirs: list[str] = []

        for directory_name in dirnames:
            candidate = current_path / directory_name

            if directory_name in excluded:
                continue
            if candidate.is_symlink():
                continue

            resolved_candidate = candidate.resolve(strict=True)
            if resolved_candidate == root or root not in resolved_candidate.parents:
                raise ValueError(f"Refusing target outside project root: {candidate}")

            if directory_name in targets:
                matches.append(resolved_candidate)
                if not dry_run:
                    shutil.rmtree(resolved_candidate)
                # Never descend into a matched directory, especially when it
                # may contain another folder with a target name.
                continue

            remaining_dirs.append(directory_name)

        dirnames[:] = remaining_dirs

    return matches


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    del_folder: list[str] = ["migrations"]
    matches = delete_folders(
        base_dir=project_root,
        del_folder=del_folder,
        excluded_dirs=DEFAULT_EXCLUDED_DIRS,
        dry_run=False,
    )

    for path in matches:
        print(f"WOULD DELETE: {path}")
    print(f"{len(matches)} directories found (dry run)")

"""

py -m utils.adapt_parts_project.delete_folders

#reinit migtations dj:
# delete_user db after lcoal.main!

for app in operator_app ad_master animation admin_comps user img_master bucket_handler certificate payment email_master system_components oasismarket; do
  mkdir -p "$app/migrations"
  touch "$app/migrations/__init__.py"
done

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
daphne oasismarket.asgi:application
"""
if __name__ == "__main__":
    main()
