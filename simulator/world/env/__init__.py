import os

from bm.settings import OS_NAME
from utils.file.yyaml import load_yaml

ENV=r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\data\uniform_env.yaml" if OS_NAME == "nt" else "utils/simulator/world/env/data/uniform_env.yaml"
ENV_LEX=r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\data\env_lex.yaml" if OS_NAME == "nt" else "utils/simulator/world/env/data/env_lex.yaml"

ENV = load_yaml(ENV)
ENV_LEX = load_yaml(ENV_LEX)

