import json
import sqlite3

def load_api_config(config_name: str) -> dict:
    with open(f"config/{config_name}.json", "r") as f:
        return json.load(f)
    
def run_sql_script(db_path: str, script_path: str):
    """
    Executes all SQL commands from a script file on the given SQLite database.

    Args:
        db_path (str): Path to the SQLite .db file.
        script_path (str): Path to the .sql file containing SQL commands.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            with open(script_path, 'r') as f:
                sql_script = f.read()
            conn.executescript(sql_script)
        print(f"Executed SQL script: {script_path}")
    except Exception as e:
        print(f"Failed to execute {script_path}: {e}")