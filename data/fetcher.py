from abc import ABC, abstractmethod
import pandas as pd
from utils.data_utils import load_api_config

class DataFetcher(ABC):
    @abstractmethod
    def fetch_data(self):
        pass

    @abstractmethod
    def store_data(self, data: pd.DataFrame):
        pass

class CSVDataFetcher(DataFetcher):
    def fetch_data(self):
        pass

    def store_data(self, data: pd.DataFrame):
        pass

class APIDataFetcher(DataFetcher, ABC):
    def __init__(self, api_config: dict):
        self.api_config = api_config

    @abstractmethod
    def fetch_data(self):
        pass

    @abstractmethod
    def store_data(self, data: pd.DataFrame):
        pass

class FinnhubAPIFetcher(APIDataFetcher):
    def __init__(self):
        super().__init__(load_api_config("finnhub"))

    def fetch_data(self):
        pass

    def store_data(self, data: pd.DataFrame):
        pass

class YahooFinanceAPIFetcher(APIDataFetcher):
    def __init__(self):
        super().__init__(load_api_config("yahoo"))

    def fetch_data(self):
        pass

    def store_data(self, data: pd.DataFrame):
        pass

def get_api_fetcher(api_name: str, config: dict) -> APIDataFetcher:
    if api_name == "yahoo":
        return YahooFinanceAPIFetcher(config)
    elif api_name == "finnhub":
        return FinnhubAPIFetcher(config)
    else:
        raise ValueError(f"Unknown API: {api_name}")