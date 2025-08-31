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
        )
        if result is not None:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print("Exit code:", e.returncode)
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
