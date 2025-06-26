from abc import ABC, abstractmethod
import pandas as pd
import time
import requests
from ingestion.storer import DataStorage, DataFrameAdapter
from utils.data_utils import load_api_config

class DataFetcher(ABC):
    @abstractmethod
    def fetch_data(self):
        pass

    @abstractmethod
    def store_data(self, data: DataFrameAdapter):
        pass

class CSVDataFetcher(DataFetcher):
    def fetch_data(self):
        pass

    def store_data(self, data: DataFrameAdapter):
        pass

class APIDataFetcher(DataFetcher, ABC):
    def __init__(self, api_config: dict, storage: DataStorage):
        self._api_config = api_config
        self._storage = storage

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
    def fetch_data(self, api_endpoint: str, headers: dict = {}, params: dict = {}):
        pass

    def store_data(self, data: DataFrameAdapter, destination: str):
        self._storage.save(data, destination)

class FinnhubAPIFetcher(APIDataFetcher):
    def __init__(self, storage: DataStorage):
        super().__init__(load_api_config("finnhub"), storage)

    def fetch_data(self, api_endpoint: str, headers: dict = {}, params: dict = {}):
        base_url = self._api_config["base_url"]
        url = f"{base_url}/{api_endpoint}"
        headers = {**headers, "X-Finnhub-Token": self._api_config["api_key"]}
        try:
            response = requests.get(url, headers=headers, params=params, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching data from Finnhub: {e}")
        
    def store_data(self, data: DataFrameAdapter, destination: str):
        return super().store_data(data, destination)

class YahooFinanceAPIFetcher(APIDataFetcher):
    def __init__(self, storage: DataStorage):
        super().__init__(load_api_config("yahoo"), storage)

    def fetch_data(self):
        pass

class FetcherFactory:
    @staticmethod
    def get_api_fetcher(api_name: str, storage: DataStorage) -> APIDataFetcher:
        if api_name == "yahoo":
            return YahooFinanceAPIFetcher(storage)
        elif api_name == "finnhub":
            return FinnhubAPIFetcher(storage)
        else:
            raise ValueError(f"Unknown API: {api_name}")