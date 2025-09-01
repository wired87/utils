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
<<<<<<< HEAD
        print("CMD result:", result)
        if result is not None:
            result = result.stdout
            print(result)
=======
        if result is not None:
            print(result.stdout)
>>>>>>> origin/master
        return result
    except subprocess.CalledProcessError as e:
        print("Exit code:", e.returncode)
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
