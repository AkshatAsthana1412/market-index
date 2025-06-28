from index.generate_index import generate_stocks_dataframe
from index.generate_index import get_sp500_tickers
from ingestion.storer import SQLiteStorage, PandasDataFrameAdapter

if __name__ == "__main__":
    tickers = get_sp500_tickers()
    print("S&P 500 tickers fetched..")
    print("Generating dataframe..")
    stocks_df = generate_stocks_dataframe(tickers)
    storer = SQLiteStorage("data/test.db")
    storer.save(PandasDataFrameAdapter(stocks_df), "stocks")
    print("Data stored successfully!!")
    
    