from pathlib import Path

import pandas as pd

# Project root is one level above this script (src/ -> Inventory_System/)
project_root = Path(__file__).resolve().parent.parent

# Folder where Partender exports live
raw_dir = project_root / "data" / "raw"

# Use the first .xlsx file found (skip Windows Zone.Identifier sidecars)
excel_files = sorted(raw_dir.glob("*.xlsx"))
if not excel_files:
    raise FileNotFoundError(f"No .xlsx files found in {raw_dir}")
excel_path = excel_files[0]

print(f"File: {excel_path.name}\n")

# Open the workbook once; sheet_names lists every tab
xl = pd.ExcelFile(excel_path)
print("Sheet names:")
print(xl.sheet_names)
print()

# Inspect each sheet
for sheet_name in xl.sheet_names:
    print("=" * 60)
    print(f"Sheet: {sheet_name}")
    print("=" * 60)

    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    print("\nColumns:")
    print(list(df.columns))

    print("\nData types:")
    print(df.dtypes)

    print("\nFirst 3 rows:")
    print(df.head(3))
    print()
