from abc import ABC, abstractmethod
from typing import TypeVar, Generic
import pandas as pd
import sqlite3


T = TypeVar('T')

class DataStorage(ABC, Generic[T]):
    @abstractmethod
    def save(self, data: T, destination: str = ""):
        pass

class CSVStorage(DataStorage[pd.DataFrame]):
    def save(self, data: pd.DataFrame, destination: str = "output.csv"):
        data.to_csv(destination, index=False)

class SQLiteStorage(DataStorage[pd.DataFrame]):
    def __init__(self, db_path="data.db"):
        self.conn = sqlite3.connect(db_path)

    def save(self, data: pd.DataFrame, destination: str = "prices"):
        data.to_sql(destination, self.conn, if_exists="replace", index=False)
