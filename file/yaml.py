import yaml

def load_yaml(filepath) -> dict:
    with open(filepath, 'r', encoding="utf-8") as file:
        data = yaml.safe_load(file)
    #print("data", data)
    return data
