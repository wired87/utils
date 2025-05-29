from bm.settings import OS_NAME
from utils.file.yyaml import load_yaml
if OS_NAME == "nt":
    ENV=r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\data\uniform_env.yaml"
    ENV_LEX=r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\simulator\world\env\data\env_lex.yaml"
else:
    ENV ="utils/simulator/world/env/data/uniform_env.yaml"
    ENV_LEX = "utils/simulator/world/env/data/env_lex.yaml"
ENV = load_yaml(ENV)
ENV_LEX = load_yaml(ENV_LEX)

