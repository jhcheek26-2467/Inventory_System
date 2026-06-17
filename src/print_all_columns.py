from pathlib import Path

import pandas as pd

excel_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "Kilroy's Sports Bar_Inventory_2025-08-12 125215-0400.xlsx"
)

df = pd.read_excel(excel_path, sheet_name="All")

for column in df.columns:
    print(column)
