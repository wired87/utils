import os
from utils.file.yyaml import load_yaml

HERE = os.path.dirname(__file__)
ENV = os.path.abspath(os.path.join(HERE, "data", "uniform_env.yaml"))
ENV_LEX = os.path.abspath(os.path.join(HERE, "data", "env_lex.yaml"))

ENV = load_yaml(ENV)
ENV_LEX = load_yaml(ENV_LEX)
