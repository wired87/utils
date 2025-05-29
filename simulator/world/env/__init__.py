# Zeile 1: Unbedingt als allererste Codezeile in der Datei!
print("DEBUG: ENTERING utils/simulator/world/env/__init__.py", flush=True)

import os # Für os.getcwd() später
from bm.settings import OS_NAME
from utils.file.yyaml import load_yaml

print(f"DEBUG env/__init__.py: OS_NAME from bm.settings is '{OS_NAME}' (Type: {type(OS_NAME)})", flush=True)
print(f"DEBUG env/__init__.py: Current PWD: {os.getcwd()}", flush=True)

if OS_NAME == "nt":
    print("DEBUG env/__init__.py: Branch 'nt' taken.", flush=True)
    ENV_PATH_FOR_LOADER = r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\data\uniform_env.yaml"
    ENV_LEX_PATH_FOR_LOADER = r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\data\env_lex.yaml"
else:
    print(f"DEBUG env/__init__.py: Branch 'else' (OS_NAME='{OS_NAME}') taken.", flush=True)
    ENV_PATH_FOR_LOADER = "utils/simulator/world/env/data/uniform_env.yaml"
    ENV_LEX_PATH_FOR_LOADER = "utils/simulator/world/env/data/env_lex.yaml"

print(f"DEBUG env/__init__.py: Path going into load_yaml for ENV: '{ENV_PATH_FOR_LOADER}'", flush=True)

# Die folgende Zeile ist laut Traceback Zeile 6 in deiner Datei (oder zumindest die, die den Fehler auslöst).
# Passe die Variablennamen ggf. an, falls du sie in deinem Code anders genannt hast als ENV_PATH_FOR_LOADER.
ENV = load_yaml(ENV_PATH_FOR_LOADER)
print("DEBUG env/__init__.py: ENV loaded successfully (this might not be reached if error above)", flush=True)

print(f"DEBUG env/__init__.py: Path going into load_yaml for ENV_LEX: '{ENV_LEX_PATH_FOR_LOADER}'", flush=True)
ENV_LEX = load_yaml(ENV_LEX_PATH_FOR_LOADER)
print("DEBUG env/__init__.py: ENV_LEX loaded successfully (this might not be reached if error above)", flush=True)

print("DEBUG: LEAVING utils/simulator/world/env/__init__.py", flush=True)