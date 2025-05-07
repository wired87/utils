from utils.file.yaml import load_yaml

EQ_BASE_P=r"C:\Users\wired\OneDrive\Desktop\Projects\Brainmaster\utils\calculations"
CORE_LAWS_P=r"\core_laws.yaml"
POSP=r"\core_laws.yaml"
GRAVITYP=r"\gravity.yaml"

CORE_LAWS_C= load_yaml(rf"{EQ_BASE_P}{CORE_LAWS_P}")
POSC= load_yaml(rf"{EQ_BASE_P}{POSP}")
GRAVITYC= load_yaml(rf"{EQ_BASE_P}{GRAVITYP}")












