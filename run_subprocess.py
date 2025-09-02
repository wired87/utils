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
        print("CMD result:", result)
        if result is not None:
            result = result.stdout.strip()
            print(result)
        return result
    except subprocess.CalledProcessError as e:
        print("Exit code:", e)

