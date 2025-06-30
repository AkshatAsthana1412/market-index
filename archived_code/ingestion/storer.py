from abc import ABC, abstractmethod
from typing import TypeVar, Generic
import sqlite3
import pandas as pd

class DataFrameAdapter(ABC):
    @abstractmethod
    def to_sql(self, table_name: str, conn):
        pass

    @abstractmethod
    def to_csv(self, destination: str):
        pass

class PandasDataFrameAdapter(DataFrameAdapter):
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def to_sql(self, table_name: str, conn, mode: str = "append"):
        self.df.to_sql(table_name, conn, if_exists=mode, index=False)

    def to_csv(self, destination: str):
        self.df.to_csv(destination, index=False)


T = TypeVar('T')

class DataStorage(ABC, Generic[T]):
    @abstractmethod
    def save(self, data: T):
        pass

class CSVStorage(DataStorage[DataFrameAdapter]):
    def __init__(self, destination: str):
        self.destination = destination

    def save(self, data: DataFrameAdapter):
        data.to_csv(self.destination, index=False)

class SQLiteStorage(DataStorage[DataFrameAdapter]):
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def save(self, data: DataFrameAdapter, table_name: str):
        data.to_sql(table_name, self.conn)
