import os
import subprocess

def exec_cmd(cmd, inp=None):
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            input=inp,
            shell=os.name == "nt",
            capture_output=True,
            timeout=20,
        )
        if result is not None:
            result = result.stdout.strip()
        # print("CMD result:", result)
        return result
    except subprocess.CalledProcessError as e:
        print("Error:", e.stderr)
        print("Output:", e.stdout)


def pop_cmd(cmd):
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}: {process}")