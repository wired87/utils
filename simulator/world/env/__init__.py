
import os # Für os.getcwd() später
from bm.settings import OS_NAME
from utils.file.yyaml import load_yaml


if OS_NAME == "nt":
    ENV_PATH_FOR_LOADER = r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\data\uniform_env.yaml"
    ENV_LEX_PATH_FOR_LOADER = r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\data\env_lex.yaml"
else:
    ENV_PATH_FOR_LOADER = "utils/simulator/world/env/data/uniform_env.yaml"
    ENV_LEX_PATH_FOR_LOADER = "utils/simulator/world/env/data/env_lex.yaml"


# Die folgende Zeile ist laut Traceback Zeile 6 in deiner Datei (oder zumindest die, die den Fehler auslöst).
# Passe die Variablennamen ggf. an, falls du sie in deinem Code anders genannt hast als ENV_PATH_FOR_LOADER.
ENV = load_yaml(ENV_PATH_FOR_LOADER)

ENV_LEX = load_yaml(ENV_LEX_PATH_FOR_LOADER)
