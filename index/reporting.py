import sqlite3
import pandas as pd
import os

def export_index_performance_to_excel(db_path="data/tmp.db", index_values_table="index_values", output_path="data/index_report.xlsx"):
    """
    Calculates daily % returns and cumulative returns from the 'index_values' table
    and exports the result to an Excel file.
    """
    query = f"""
    WITH returns AS (
      SELECT
        date,
        value,
        LAG(value) OVER (ORDER BY date) AS prev_value
      FROM {index_values_table}
    ),
    daily_returns AS (
      SELECT
        date,
        value,
        ROUND(((value * 1.0 / prev_value) - 1) * 100, 4) AS daily_pct_return,
        ROUND((value * 1.0 / FIRST_VALUE(value) OVER (ORDER BY date) - 1) * 100, 4) AS cumulative_pct_return
      FROM returns
      WHERE prev_value IS NOT NULL
    )
    SELECT * FROM daily_returns ORDER BY date;
    """

    # Query the SQLite database
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Export to Excel, create if not exists
    if not os.path.exists(output_path):
        with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
            df.to_excel(writer, sheet_name="index_performance", index=False)
    else:
        with pd.ExcelWriter(output_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name="index_performance", index=False)
    print(f"Exported index performance to {output_path}")


def export_index_composition_to_excel(db_path="data/tmp.db", output_path="data/index_report.xlsx"):
    # Load data
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT date, tickers FROM index_stocks ORDER BY date, tickers", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    grouped = df.groupby("date")["tickers"].apply(list).sort_index()
    composition_df = grouped.to_frame(name="tickers")

    # Export with overwrite sheet
    with pd.ExcelWriter(output_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        composition_df.to_excel(writer, sheet_name="index_composition")

    print(f"Exported index composition to {output_path}")

def export_index_summary_to_excel(db_path="data/tmp.db", index_values_table="index_values", output_path="data/index_report.xlsx"):
    """
    Executes SQL-only logic to compute:
    - latest index value
    - best/worst day by daily % return
    - total cumulative return
    And exports results to Excel.
    """
    sql = f"""
    WITH ranked AS (
      SELECT
        date,
        value,
        LAG(value) OVER (ORDER BY date) AS prev_value,
        FIRST_VALUE(value) OVER (ORDER BY date) AS base_value,
        LAST_VALUE(value) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS latest_value,
        LAST_VALUE(date) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS latest_date
      FROM {index_values_table}
    ),
    returns AS (
      SELECT *,
             ((value * 1.0 / prev_value) - 1) * 100 AS daily_pct_return,
             ((latest_value * 1.0 / base_value) - 1) * 100 AS aggregate_return
      FROM ranked
      WHERE prev_value IS NOT NULL
    ),
    best AS (
      SELECT date AS best_day, ROUND(daily_pct_return, 2) AS best_day_return
      FROM returns
      ORDER BY daily_pct_return DESC LIMIT 1
    ),
    worst AS (
      SELECT date AS worst_day, ROUND(daily_pct_return, 2) AS worst_day_return
      FROM returns
      ORDER BY daily_pct_return ASC LIMIT 1
    ),
    latest AS (
      SELECT DISTINCT latest_date AS latest_date, ROUND(latest_value, 2) AS latest_value, ROUND(aggregate_return, 2) AS aggregate_return
      FROM returns
    )
    SELECT 
      latest.latest_date AS "Latest Date",
      latest.latest_value AS "Latest Index Value",
      best.best_day AS "Best Day",
      best.best_day_return AS "Best Day Return (%)",
      worst.worst_day AS "Worst Day",
      worst.worst_day_return AS "Worst Day Return (%)",
      latest.aggregate_return AS "Aggregate Return (%)"
    FROM latest, best, worst;
    """

    # Query DB
    conn = sqlite3.connect(db_path)
    summary_df = pd.read_sql_query(sql, conn)
    conn.close()

    # Write to Excel
    if not os.path.exists(output_path):
        with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
            summary_df.to_excel(writer, sheet_name="index_summary", index=False)
    else:
        with pd.ExcelWriter(output_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            summary_df.to_excel(writer, sheet_name="index_summary", index=False)

    print(f"Exported index summary to '{output_path}'")
    
    