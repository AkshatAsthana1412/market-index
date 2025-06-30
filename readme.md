# 📊 Project Overview

This project builds and tracks a custom equal-weighted index composed of the top 100 U.S. stocks by market capitalization. The index is updated daily to reflect changes in market cap, ensuring each constituent maintains an equal notional weight.

Key features include:
* Dynamic daily rebalancing based on updated market cap data
* Accurate calculation of index performance and composition over the past month
* Clean, modular Python codebase with extensible architecture
* Final output in a well-formatted Excel report


## Steps to run the code:
* Install the requirements from the requirements.txt by running the following command on the terminal : `pip3 install -r requirements.txt`
* I used python 3.12 for dev. 
* to run the project, run the command: python3 main.py <start_date> <end_date> <path_to_sqlite_db_file>
* The dates should be in `"YYYY-MM-DD"` format, default path to sqlite db file is `data/tmp.db`.
* Unfortunately due to time constraints, I couldn't create an airflow dag which would run the pipeline every day after market close.
* To get data for a single day, use equal values for start and end date
* All the data used to generate the reports from 1 Jun to 27 Jun is already stored in the `data/tmp.db` file. Feel free to query it using sqlite3 CLI.
  
  ```
  Example usage of the sqlite3 cli, navigate to the root directory of this repo on the command line, then run:
  
  > sqlite3 data/tmp.db

  this will open the sqlite terminal, where you may run SQL queries.
  
  Please check SQLite documentation for more info.
  ```
* The excel reports can be found inside the `data` folder. (`index_report.xlsx`)

## Choice of data source
* After exploring several data sources like **IEX Cloud, Finnhub, Yfinance, Quandl**. I picked Yfinance because it's free, easy to use, good coverage of US stocks, options etc.,very good for quick prototyping, bulk download for multiple tickers through *yf.download* module, free availability of historical data and good community support on the web (e.g.: https://algotrading101.com/learn/yfinance-guide/)
  
## Challenges
* **Figuring out the top 100 stocks to include in my custom index.**
  * To pick the top 100 stocks list, the naive approach would have been to fetch a list of all publicly listed US stocks, somehow calculate their market cap everyday and then select the top 100 from among them with the highest market cap. This would be very computationally intense, since there are more than 4000 publicly listed US companies.
  * Instead I chose to fetch the stocks in S&P 500 everyday and calculate their market caps followed by selecting the top 100 stocks from this list everyday. I chose S&P500 because it consists of the top 500 publicly listed US companies with the largest market cap, so our top 100 stocks will very likely be in this list.
* **Calculating historical market cap**
  * At first I decided to use the yf.ticker module to fetch market cap data everyday, but the problem was it returns a snapshot of the current market data of a given ticker, which would not work if we wanted to backfill.
  * So I rewrote my logic to fetch market data using yf.download module, which allows to specify a date range, but it doesn't provide market cap values directly in the response.
  * To solve the above problem I used a combination of yf.ticker and yf.download.
  * I used yf.ticker to fetch *sharesOutstanding* for each ticker in S&P500 and yf.donwload to fetch *Close* price for each ticker, then calculated `marketCap = sharesOutstanding * Close`.
* **Market holidays**
  * I didn't initially consider market holidays in my index generation logic.
  * The index tables(`index_values, index_stocks`) expect T-1 day data to work correctly.
  * To solve this problem, for each market holiday, I carry forward the last available day data in the `stocks_base` table. I use a lookback period(default=10 days) to check the last market open day.
  * This makes sure the index generation logic doesn't break and the index simply reflects 0% change on subsequent market close days.
  
## Brief design overview:
* The pipeline starts by scraping wikipedia for the latest list of S&P500 tickers, this can be reduced to once a month since S&P list doesn't change as frequently.
* These tickers are then used to fetch OCHLV data from yfinance.download module and SharesOutstanding data from yfinance.Tickers module.
* The sharesOutstanding data can also be cached and fetched once a week/month, since it's slowly changing. This can reduce the pipeline processing time.
* Using close price and sharesOutstanding, I calculate the market cap of each company each day and store it in `stocks_base` table in a SQLite database.
* From the `stocks_base` table, our custom index is created. Each day, the `index_value` and `index_stocks` tables are updated and index is rebalanced. Top 100 stocks from the `stocks_base` table are selected to be put in the index and based on their T-1 day close price, daily returns are calculated for the index.
* The excel reports for tracking daily index_performance, index composition and summary metrics are created using the above fact tables. Currently the code does a full refresh of the reports instead of appending new records. (This can be improved in later iterations).
* The `index/populate_fact_tables` and `index/reporting` modules host the functions to do all the necessary processing. The `main.py` file is the entry point of the program. 


## Furthur improvements:
* Instead of the `main.py` file acting as an entry, and running CLI commands to run the pipeline, the pipeline can be orchestrated via airflow, which can also provide alerting and monitoring mechanisms, making observability easier.
* With increasing data size/index size, a big data processing framework like apache spark could be used for imporved parallelism, though it will need code refactoring.
* The sharesOutstanding values can be fetched concurrently to improve ingestion times. 
* Real time rebalancing of the index during market hours could be done, but it would need fast, reliable data sources which have high rate limits or websocket interfaces to fetch price data in real time.
* As the data size increases, we can switch to cloud storage or cloud datawarehouse to save storage costs.
* The ingestion logic can be written in golang for faster processing and more efficient concurrency support.
* I initially tried to code an ingestion framework where any API could be plugged and data could be fetched and stored in a variety of destinations(csv, DBs etc.), but due to time constraints and unavailability of free APIs, I abandoned that approach. (That code can still be found in `archived_code` dir.)
