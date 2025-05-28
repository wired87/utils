import os

from utils.file.yyaml import load_yaml
ENV=r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\uniform_env.yaml"
ENV_LEX=r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\env_lex.yaml" if os.name == "nt" else "utils/simulator/world/env/env_lex.yaml"
ENV = load_yaml(ENV)
ENV_LEX = load_yaml(ENV_LEX)

