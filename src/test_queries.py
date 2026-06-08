import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Allow `python src/test_queries.py` from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from queries import (
    get_available_snapshot_dates,
    get_below_par_products,
    get_inventory_value_by_category,
    get_inventory_value_by_distributor,
    get_inventory_value_by_location,
    get_inventory_value_by_product,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

SNAPSHOT_DATE = "2025-12-19"

# Show all columns when printing DataFrames (avoid "..." truncation)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)


def run_query(title, df):
    print("=" * 60)
    print(title)
    print("=" * 60)
    if df.empty:
        print("(no rows)")
    else:
        print(df.head(10).to_string(index=False))
    print()


with engine.connect() as conn:
    run_query(
        "get_inventory_value_by_product",
        get_inventory_value_by_product(conn, SNAPSHOT_DATE),
    )

    run_query(
        "get_inventory_value_by_location",
        get_inventory_value_by_location(conn, SNAPSHOT_DATE),
    )

    run_query(
        "get_inventory_value_by_category",
        get_inventory_value_by_category(conn, SNAPSHOT_DATE),
    )

    run_query(
        "get_inventory_value_by_distributor",
        get_inventory_value_by_distributor(conn, SNAPSHOT_DATE),
    )

    run_query(
        "get_below_par_products",
        get_below_par_products(conn, SNAPSHOT_DATE),
    )

    run_query(
        "get_available_snapshot_dates",
        get_available_snapshot_dates(conn),
    )

print("All queries complete.")
