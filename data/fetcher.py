from abc import ABC, abstractmethod
import pandas as pd
from utils.data_utils import load_api_config
import time
import requests

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
        self._api_config = api_config

    def _with_retries(self, func, max_retries=3, delay=1, backoff=2, *args, **kwargs):
        """
        Helper method to retry a function call with exponential backoff on failure.
        Available for subclasses to use for retryable API calls.
        """
        attempt = 0
        current_delay = delay
        while attempt < max_retries:
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, Exception) as e:
                attempt += 1
                if attempt == max_retries:
                    raise
                time.sleep(current_delay)
                current_delay *= backoff

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

class FetcherFactory:
    @staticmethod
    def get_api_fetcher(api_name: str) -> APIDataFetcher:
        if api_name == "yahoo":
            return YahooFinanceAPIFetcher()
        elif api_name == "finnhub":
            return FinnhubAPIFetcher()
        else:
            raise ValueError(f"Unknown API: {api_name}")