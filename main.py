from index.populate_fact_tables import update_stocks_base_table, update_index
from index.populate_fact_tables import get_sp500_tickers
import sys
import pandas as pd
from index.reporting import export_index_performance_to_excel, export_index_composition_to_excel, export_index_summary_to_excel

if __name__ == "__main__":
    start_date, end_date, db_path = sys.argv[1], sys.argv[2], sys.argv[3]
    tickers = get_sp500_tickers()
    print("S&P 500 tickers fetched..")
    for dt in pd.date_range(start_date, end_date):
        update_stocks_base_table(dt.strftime("%Y-%m-%d"), tickers, db_path)
        print(f"Stocks base table updated successfully for {dt}!!")
        update_index(dt.strftime("%Y-%m-%d"), db_path)   
        print(f"Index tables updated successfully for {dt}!!")
        print("Exporting index performance to excel..")
        export_index_performance_to_excel(db_path)
        print("Exporting index composition to excel..")
        export_index_composition_to_excel(db_path)
        print("Exporting index summary to excel..")
        export_index_summary_to_excel(db_path)

    
    
    