import json

def load_api_config(config_name: str) -> dict:
    with open(f"config/{config_name}.json", "r") as f:
        return json.load(f)