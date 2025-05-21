import yaml

def load_yaml(filepath) -> dict:
    with open(filepath, 'r', encoding="utf-8") as file:
        data = yaml.safe_load(file)
    #print("data", data)
    return data


def save_yaml(filepath, data) -> dict:
    with open(filepath, "w", encoding="utf-8") as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)
    #print("data", data)
    return data
