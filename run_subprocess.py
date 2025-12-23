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
            timeout=120, # Increased timeout for Windows
        )
        if result is not None:
            result = result.stdout.strip()
        # print("CMD result:", result)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command {cmd}: {e.stderr}")
        print("Output:", e.stdout)
        return None
    except subprocess.TimeoutExpired as e:
        print(f"Command timed out {cmd} after {e.timeout} seconds")
        if e.stdout: print("Output so far:", e.stdout.decode())
        if e.stderr: print("Error so far:", e.stderr.decode())
        return None
    except Exception as e:
        print(f"Unexpected error executing {cmd}: {e}")
        return None


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