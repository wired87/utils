import os
import shlex
import subprocess


def exec_cmd(
        cmd,
        inp=None,
        *,
        cwd=None,
        env=None,
        timeout=120,
        check=True,
        capture_output=True,
        wait=True,
):
    """Run a command, optionally streaming it like a manual terminal command.

    Attempts to run the executable from the local .venv first. If it fails or does not exist,
    it falls back to standard execution behavior.
    """
    # 1. Vorbereitung der Argumente
    if isinstance(cmd, (list, tuple)):
        raw_args = [str(part) for part in cmd]
    elif os.name == "nt":
        raw_args = [str(cmd)]
    else:
        raw_args = shlex.split(str(cmd))

    # 2. Versuch: Venv-Pfad ermitteln
    venv_args = None
    if raw_args:
        executable = raw_args[0]
        # .venv Verzeichnis relativ zur aktuellen Datei oder CWD ermitteln
        base_dir = cwd or os.getcwd()

        # Betriebssystem-spezifischer Pfad für .venv Executables
        if os.name == "nt":
            venv_bin_dir = os.path.join(base_dir, ".venv", "Scripts")
            # Prüfe auf .exe, .bat, .cmd Erweiterungen unter Windows
            candidate_names = [executable, f"{executable}.exe", f"{executable}.bat", f"{executable}.cmd"]
        else:
            venv_bin_dir = os.path.join(base_dir, ".venv", "bin")
            candidate_names = [executable]

        # Suchen nach dem Executable im .venv Ordner
        venv_executable = None
        for name in candidate_names:
            possible_path = os.path.join(venv_bin_dir, name)
            if os.path.isfile(possible_path) and os.access(possible_path, os.X_OK):
                venv_executable = possible_path
                break

        if venv_executable:
            venv_args = [venv_executable] + raw_args[1:]

    # Hilfsfunktion zur Formatierung der Args je nach OS & Shell-Modus
    def format_args(args_list):
        if os.name == "nt" and len(args_list) == 1:
            return args_list[0]
        return args_list

    # 3. Haupt-Ausführungslogik mit .venv-Try und Fallback
    try_args_list = []
    if venv_args:
        try_args_list.append(venv_args)  # Priorität 1: Local .venv Executable
    try_args_list.append(raw_args)  # Priorität 2: Fallback (System-PATH / Original)

    for current_args in try_args_list:
        args = format_args(current_args)
        shell = isinstance(args, str)
        common = {
            "cwd": cwd,
            "env": env,
            "shell": shell,
            "text": True,
        }

        if not wait:
            if inp is not None:
                raise ValueError("inp cannot be used with wait=False")
            if capture_output:
                common.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                return subprocess.Popen(args, **common)
            except Exception:
                if current_args == try_args_list[-1]:  # Letzter Versuch fehlgeschlagen
                    raise
                continue  # Weiter zum Fallback

        try:
            result = subprocess.run(
                args,
                check=check,
                input=inp,
                capture_output=capture_output,
                timeout=timeout,
                **common,
            )
            if capture_output:
                return result.stdout.strip()
            return result
        except FileNotFoundError:
            # Wenn das Executable im .venv nicht gestartet werden konnte -> Nächster Fallback-Versuch
            if current_args != try_args_list[-1]:
                continue
            print(f"Executable not found for command: {cmd}")
            return None
        except subprocess.CalledProcessError as exc:
            if not check:
                return exc
            print(f"Error executing command {cmd}: {exc.stderr or ''}")
            print("Output:", exc.stdout or "")
            return None
        except subprocess.TimeoutExpired as exc:
            print(f"Command timed out {cmd} after {exc.timeout} seconds")
            if exc.stdout:
                print("Output so far:", exc.stdout)
            if exc.stderr:
                print("Error so far:", exc.stderr)
            return None
        except Exception as exc:
            if current_args != try_args_list[-1]:
                continue
            print(f"Unexpected error executing {cmd}: {exc}")
            return None

    return None


def pop_cmd(cmd, cwd=None):
    """Run a command and stream its merged stdout/stderr."""
    is_windows = os.name == "nt"
    if isinstance(cmd, (list, tuple)):
        args_list = [str(c) for c in cmd]
    else:
        args_list = [str(cmd)]
    display_cmd = " ".join(args_list)

    popen_kw = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if cwd is not None:
        popen_kw["cwd"] = cwd

    try:
        process = subprocess.Popen(
            display_cmd if is_windows else args_list,
            shell=is_windows,
            **popen_kw,
        )
        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
            print(line, end="")
        process.wait()
        if process.returncode != 0:
            combined_output = "".join(output_lines)
            if is_windows and "dockerDesktopLinuxEngine" in combined_output:
                raise RuntimeError(
                    "Docker engine is not running. Please start Docker Desktop "
                    "and ensure the Linux engine is enabled, then retry.\n"
                    f"Command: {display_cmd}"
                )
            raise RuntimeError(
                f"Command failed with exit code {process.returncode}: {display_cmd}"
            )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Command not found: {args_list[0]}. Is it installed and on your PATH?"
        ) from exc
