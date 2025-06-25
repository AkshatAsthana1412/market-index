from abc import ABC, abstractmethod
import pandas as pd
import sqlite3

class DataStorage(ABC):
    @abstractmethod
    def save(self, data: pd.DataFrame, destination: str = ""):
        pass

class CSVStorage(DataStorage):
    def save(self, data: pd.DataFrame, destination: str = "output.csv"):
        data.to_csv(destination, index=False)

class SQLiteStorage(DataStorage):
    def __init__(self, db_path="data.db"):
        self.conn = sqlite3.connect(db_path)

    def save(self, data: pd.DataFrame, destination: str = "prices"):
        data.to_sql(destination, self.conn, if_exists="replace", index=False)
