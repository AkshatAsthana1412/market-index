import requests
import pandas as pd
from io import StringIO
import yfinance as yf
from requests_ratelimiter import LimiterSession
from ratelimit import limits, sleep_and_retry
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import sqlite3

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

def get_latest_available_data(tickers: list, date: str, max_lookback: int = 10) -> pd.DataFrame:
    """
    Fetches OHLCV data for the given date. If it's a holiday or weekend, returns the most recent valid trading day.
    
    Args:
        tickers (list): List of stock symbols.
        date (str): Target date in 'YYYY-MM-DD' format.
        max_lookback (int): How many days back to try if data is missing.
    
    Returns:
        pd.DataFrame: DataFrame containing OHLCV data for the found date.
    """
    target_date = pd.to_datetime(date).date()

    for _ in range(max_lookback):
        start = target_date
        end = target_date + timedelta(days=1)

        df = yf.download(
            tickers=" ".join(tickers),
            start=start.isoformat(),
            end=end.isoformat(),
            interval="1d",
            threads=True,
            auto_adjust=False
        )

        # Check if data was returned
        if not df.empty:
            print(f"Data found for {target_date}")
            return df

        # If no data, step back one day
        target_date -= timedelta(days=1)

    raise ValueError(f"No valid data found within {max_lookback} days before {date}")


def update_stocks_base_table(dt: str, tickers: list, db_path: str, table_name: str = "stocks_base") -> pd.DataFrame:
    """
    Parses the latest data and updates the stocks base table for index generation.
    """
    # get latest available data
    latest_stocks_df = get_latest_available_data(tickers, dt)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # create table if it doesn't exist
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (date TEXT, ticker TEXT, close REAL, shares_outstanding REAL, market_cap REAL);")
    
    # check if stocks table has data for today
    cursor.execute(f"SELECT 1 FROM {table_name} WHERE date = ?", (dt,))
    if cursor.fetchone():
        print(f"Stocks table has data for {dt}. Skipping...")
        conn.close()
        return
    
    # Fetch shares outstanding for each ticker
    shares_lookup = {}
    print("Fetching shares outstanding for each ticker in S&P500..")
    for ticker in tickers:
        try:
            shares = yf.Ticker(ticker).info.get("sharesOutstanding")
            if shares:
                shares_lookup[ticker] = shares
            time.sleep(0.5) 
        except Exception as e:
            print(f"{ticker}: {e}")
            continue

    print('Calculating market cap...')
    rows = []
    for ticker in tickers:
        try:
            close_series = latest_stocks_df["Close"][ticker]
            for _, close in close_series.items():
                if pd.notna(close):
                    rows.append({
                        "date": pd.to_datetime(dt).date(),
                        "ticker": ticker,
                        "close": close,
                        "shares_outstanding": shares_lookup[ticker],
                        "market_cap": close * shares_lookup[ticker]
                    })
        except KeyError:
            print(f"No data for {ticker}")
            continue
    stocks_df = pd.DataFrame(rows)
    # Store the data in the database
    stocks_df.to_sql(table_name, conn, if_exists="append", index=False)
    conn.close()
    return stocks_df



def update_index(today_str: str, db_path: str = "data/test.db", stocks_base_table: str = "stocks_base", index_values_table: str = "index_values", index_stocks_table: str = "index_stocks"):
    """
    Computes and stores the equal-weighted index value for the given day.
    """
    if today_str is None:
        today = datetime.today().date()
    else:
        today = datetime.strptime(today_str, "%Y-%m-%d").date()

    yesterday = today - timedelta(days=1)
    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {index_values_table} (date TEXT PRIMARY KEY, value REAL);")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {index_stocks_table} (tickers TEXT, date TEXT);")

    # Check if index for today already exists
    cursor.execute(f"SELECT 1 FROM {index_values_table} WHERE date = ?", (today_str,))
    if cursor.fetchone():
        print(f"Index for {today_str} already exists.")
        conn.close()
        return
    
    # check if stocks table has data for yesterday
    cursor.execute(f"SELECT 1 FROM {stocks_base_table} WHERE date = ?", (yesterday_str,))
    if not cursor.fetchone():
        print(f"Stocks table has no data for {yesterday_str}")
        index_value_today = 100.0
    else:
        # Get yesterday's index value (default to 100 if not available)
        cursor.execute(f"SELECT value FROM {index_values_table} WHERE date = ?", (yesterday_str,))
        row = cursor.fetchone()
        index_value_yesterday = row[0] if row else 100.0
        # Run SQL to compute today's index using equal-weighted average return
        sql = f"""
        WITH top100_today AS (
            SELECT * FROM {stocks_base_table}
            WHERE date = ?
            ORDER BY market_cap DESC
            LIMIT 100
        ),
        top100_yesterday AS (
            SELECT * FROM {stocks_base_table}
            WHERE date = ?
            AND ticker IN (SELECT ticker FROM top100_today)
        ),
        returns AS (
            SELECT
                t.ticker,
                t.close AS close_today,
                y.close AS close_yesterday,
                (t.close * 1.0 / y.close) - 1 AS daily_return
            FROM top100_today t
            JOIN top100_yesterday y ON t.ticker = y.ticker
            WHERE y.close > 0
        )
        SELECT ROUND(AVG(1 + daily_return) * ?, 2) AS index_value_today
        FROM returns;
        """
        
        cursor.execute(sql, (today_str, yesterday_str, index_value_yesterday))
        result = cursor.fetchone()
        index_value_today = result[0] if result else None

    if index_value_today is None:
        print(f"Could not compute index for {today_str}")
    else:
        # Store the result in the index_values table
        cursor.execute(
            f"INSERT OR REPLACE INTO {index_values_table} (date, value) VALUES (?, ?)",
            (today_str, index_value_today)
        )
        conn.commit()
        print(f"Stored index value for {today_str}: {index_value_today}")

    # Store the top 100 tickers for today
    cursor.execute(f"SELECT 1 FROM {index_stocks_table} WHERE date = ?", (today_str,))
    if cursor.fetchone():
        print(f"Stocks index for {today_str} already exists.")
    else:
        store_top100_today = f"""
        INSERT OR REPLACE INTO {index_stocks_table} (tickers, date)
        SELECT ticker, date FROM {stocks_base_table}
            WHERE date = ?
            ORDER BY market_cap DESC
            LIMIT 100
        """
        cursor.execute(store_top100_today, (today_str,))
        conn.commit()
        print(f"Stocks index for {today_str} stored successfully.")

    conn.close()



# # 1 call per second = 60 calls per minute
# RATE_LIMIT = 1  # requests per second

# # Rate-limited requests session
# session = LimiterSession(per_second=RATE_LIMIT)

# # Rate-limit decorator for yfinance calls
# @sleep_and_retry
# @limits(calls=RATE_LIMIT, period=1)
# def get_ticker_info(ticker):
#     try:
#         info = yf.Ticker(ticker).info
#         market_cap = info.get("marketCap", 0)
#         return ticker, market_cap
#     except Exception as e:
#         print(f"Error fetching market cap for {ticker}: {e}")
#         return ticker, 0


# def update_stocks_base_table(tickers:list, db_path: str):
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute("SELECT 1 FROM stocks WHERE date = ?", (datetime.today().strftime('%Y-%m-%d'),))
#     if cursor.fetchone():
#         print(f"Stocks for {datetime.today().strftime('%Y-%m-%d')} already exists. Skipping...")
#         conn.close()
#         return
#     else:
#         with ThreadPoolExecutor(max_workers=10) as executor:
#             results = list(executor.map(get_ticker_info, tickers))
#         df = pd.DataFrame(results, columns=["ticker", "market_cap"])
#         df["date"] = datetime.today().strftime('%Y-%m-%d')
#         df.to_sql("stocks", conn, if_exists="append", index=False)
#         conn.close()