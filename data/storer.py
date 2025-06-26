from abc import ABC, abstractmethod
from typing import TypeVar, Generic
import sqlite3
import pandas as pd

class DataFrameAdapter(ABC):
    @abstractmethod
    def to_sql(self, destination: str, conn):
        pass

    @abstractmethod
    def to_csv(self, destination: str):
        pass

class PandasDataFrameAdapter(DataFrameAdapter):
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def to_sql(self, destination: str, conn):
        self.df.to_sql(destination, conn, if_exists="replace", index=False)

    def to_csv(self, destination: str):
        self.df.to_csv(destination, index=False)


T = TypeVar('T')

class DataStorage(ABC, Generic[T]):
    @abstractmethod
    def save(self, data: T, destination: str):
        pass

class CSVStorage(DataStorage[DataFrameAdapter]):
    def save(self, data: DataFrameAdapter, destination: str):
        data.to_csv(destination, index=False)

class SQLiteStorage(DataStorage[DataFrameAdapter]):
    def __init__(self, db_path="data.db"):
        self.conn = sqlite3.connect(db_path)

    def save(self, data: DataFrameAdapter, destination: str):
        data.to_sql(destination, conn=self.conn)
