import requests
import pandas as pd
from io import StringIO
import yfinance as yf
from requests_ratelimiter import LimiterSession
from ratelimit import limits, sleep_and_retry
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def get_sp500_tickers() -> list:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers, timeout=10, verify=False)
    response.raise_for_status()  # raise an exception on HTTP error

    tables = pd.read_html(StringIO(response.text))
    df = tables[0]

    tickers = df["Symbol"].tolist()
    tickers = [t.replace(".", "-") for t in tickers]  # Yahoo compatibility
    return tickers


# 1 call per second = 60 calls per minute
RATE_LIMIT = 1  # requests per second

# Rate-limited requests session
session = LimiterSession(per_second=RATE_LIMIT)

# Rate-limit decorator for yfinance calls
@sleep_and_retry
@limits(calls=RATE_LIMIT, period=1)
def get_market_cap(ticker):
    try:
        info = yf.Ticker(ticker).info
        market_cap = info.get("marketCap", 0)
        open = info.get("open", 0)
        close = info.get("close", 0)
        day_high = info.get("dayHigh", 0)
        day_low = info.get("dayLow", 0)
        volume = info.get("volume", 0)
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        country = info.get("country", "")
        return ticker, market_cap, open, close, day_high, day_low, volume, sector, industry, country
    except Exception as e:
        print(f"Error fetching market cap for {ticker}: {e}")
        return ticker, 0


def generate_stocks_dataframe(tickers:list) -> pd.DataFrame:
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_market_cap, tickers))
    df = pd.DataFrame(results, columns=["ticker", "market_cap", "open", "close", "day_high", "day_low", "volume", "sector", "industry", "country"])
    df["date"] = datetime.today().strftime('%Y-%m-%d')
    return df
    
    