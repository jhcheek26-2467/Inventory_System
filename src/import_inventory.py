import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

project_root = Path(__file__).resolve().parent.parent
raw_dir = project_root / "data" / "raw"

# Partender filenames contain _Inventory_YYYY-MM-DD before the time stamp
DATE_PATTERN = re.compile(r"_Inventory_(\d{4}-\d{2}-\d{2})")
TIMESTAMP_PATTERN = re.compile(r"_Inventory_\d{4}-\d{2}-\d{2}\s+(\d{6})")

# Quantity columns on the All sheet → location_name in the locations table
LOCATION_QUANTITY_COLUMNS = [
    "Circle Bar Quantity",
    "Main Bar Quantity",
    "Garage Bar Quantity",
    "Ice Bar Quantity",
    "Rooftop Bar Quantity",
    "Jungle Bar Quantity",
    "Dry Storage Quantity",
    "VIP Quantity",
    "BIBs Quantity",
    "DO NOT TOUCH Quantity",
]

SNAPSHOT_INSERT = text(
    """
    INSERT INTO inventory_snapshots (
        snapshot_date,
        product_id,
        location_id,
        quantity
    )
    VALUES (
        :snapshot_date,
        :product_id,
        :location_id,
        :quantity
    )
    """
)

SNAPSHOT_CHUNK_SIZE = 500


def to_text(value):
    """Convert Excel floats (e.g. 12345.0) to clean text; missing → None."""
    if pd.isna(value):
        return None
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    text_value = str(value).strip()
    return text_value if text_value else None


def to_int(value):
    if pd.isna(value):
        return None
    return int(value)


def to_float(value):
    if pd.isna(value):
        return None
    return float(value)


def parse_filename(filename):
    """Return (snapshot_date, timestamp) from a Partender export filename."""
    date_match = DATE_PATTERN.search(filename)
    if not date_match:
        return None
    timestamp_match = TIMESTAMP_PATTERN.search(filename)
    timestamp = timestamp_match.group(1) if timestamp_match else "000000"
    return date_match.group(1), timestamp


def import_file(excel_path):
    """Run the full ETL pipeline for one Partender Excel export."""
    excel_path = Path(excel_path)

    parsed = parse_filename(excel_path.name)
    if not parsed:
        raise ValueError(
            f"Could not find date in filename (expected _Inventory_YYYY-MM-DD): {excel_path.name}"
        )
    snapshot_date, _timestamp = parsed

    print(f"Importing: {excel_path.name}")
    print(f"Snapshot date: {snapshot_date}")

    df = pd.read_excel(excel_path, sheet_name="All")
    print(f"Loaded {len(df)} product rows from All sheet")

    with engine.begin() as conn:
        distributor_names = (
            df["Distributor"].dropna().astype(str).str.strip().unique().tolist()
        )
        distributor_id_by_name = {}

        for name in distributor_names:
            if not name:
                continue
            row = conn.execute(
                text(
                    """
                    INSERT INTO distributors (distributor_name)
                    VALUES (:name)
                    ON CONFLICT (distributor_name) DO UPDATE
                        SET distributor_name = EXCLUDED.distributor_name
                    RETURNING distributor_id
                    """
                ),
                {"name": name},
            ).fetchone()
            distributor_id_by_name[name] = row[0]

        print(f"Upserted {len(distributor_id_by_name)} distributors")

        category_names = (
            df["Selected Product Category"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )
        category_id_by_name = {}

        for name in category_names:
            if not name:
                continue
            row = conn.execute(
                text(
                    """
                    INSERT INTO categories (category_name)
                    VALUES (:name)
                    ON CONFLICT (category_name) DO UPDATE
                        SET category_name = EXCLUDED.category_name
                    RETURNING category_id
                    """
                ),
                {"name": name},
            ).fetchone()
            category_id_by_name[name] = row[0]

        print(f"Upserted {len(category_id_by_name)} categories")

        existing_products = conn.execute(
            text(
                """
                SELECT product_id, product_name, container_size_ml
                FROM products
                """
            )
        ).fetchall()

        product_id_by_key = {}
        for product_id, product_name, container_size_ml in existing_products:
            product_id_by_key[(product_name, container_size_ml)] = product_id

        product_ids_for_snapshots = []

        for _, row in df.iterrows():
            product_name = row["Product Name"]
            if pd.isna(product_name) or not str(product_name).strip():
                continue

            product_name = str(product_name).strip()
            container_size_ml = to_int(row["Container Size (mL)"])
            product_key = (product_name, container_size_ml)

            distributor_name = row["Distributor"]
            distributor_id = None
            if pd.notna(distributor_name):
                distributor_name = str(distributor_name).strip()
                if distributor_name:
                    distributor_id = distributor_id_by_name.get(distributor_name)

            category_name = row["Selected Product Category"]
            category_id = None
            if pd.notna(category_name):
                category_name = str(category_name).strip()
                if category_name:
                    category_id = category_id_by_name.get(category_name)

            product_values = {
                "product_name": product_name,
                "product_code": to_text(row["Product Code"]),
                "bin_number": to_text(row["Bin Number"]),
                "container_size_ml": container_size_ml,
                "distributor_id": distributor_id,
                "category_id": category_id,
                "wholesale_cost_per_unit": to_float(row["Wholesale Cost/Unit ($)"]),
                "avg_retail_price_per_serving": to_float(
                    row["Average Retail Price/Serving ($)"]
                ),
                "par": to_float(row["Par"]),
            }

            if product_key in product_id_by_key:
                product_id = product_id_by_key[product_key]
                conn.execute(
                    text(
                        """
                        UPDATE products
                        SET product_code = :product_code,
                            bin_number = :bin_number,
                            distributor_id = :distributor_id,
                            category_id = :category_id,
                            wholesale_cost_per_unit = :wholesale_cost_per_unit,
                            avg_retail_price_per_serving = :avg_retail_price_per_serving,
                            par = :par
                        WHERE product_id = :product_id
                        """
                    ),
                    {**product_values, "product_id": product_id},
                )
            else:
                result = conn.execute(
                    text(
                        """
                        INSERT INTO products (
                            product_name,
                            product_code,
                            bin_number,
                            container_size_ml,
                            distributor_id,
                            category_id,
                            wholesale_cost_per_unit,
                            avg_retail_price_per_serving,
                            par
                        )
                        VALUES (
                            :product_name,
                            :product_code,
                            :bin_number,
                            :container_size_ml,
                            :distributor_id,
                            :category_id,
                            :wholesale_cost_per_unit,
                            :avg_retail_price_per_serving,
                            :par
                        )
                        RETURNING product_id
                        """
                    ),
                    product_values,
                )
                product_id = result.fetchone()[0]
                product_id_by_key[product_key] = product_id

            product_ids_for_snapshots.append(product_id)

        print(f"Upserted {len(product_ids_for_snapshots)} products")

        missing_location_columns = [
            col for col in LOCATION_QUANTITY_COLUMNS if col not in df.columns
        ]
        if len(missing_location_columns) > len(LOCATION_QUANTITY_COLUMNS) / 2:
            raise ValueError(
                "File appears to use a different location structure than expected — skipping"
            )

        if missing_location_columns:
            for col in missing_location_columns:
                df[col] = 0.0
            print(
                "Added missing location columns filled with 0.0: "
                + ", ".join(missing_location_columns)
            )

        snapshot_df = df[
            ["Product Name", "Container Size (mL)"] + LOCATION_QUANTITY_COLUMNS
        ].copy()
        snapshot_df["product_key"] = list(
            zip(
                snapshot_df["Product Name"].astype(str).str.strip(),
                snapshot_df["Container Size (mL)"].apply(to_int),
            )
        )
        snapshot_df["product_id"] = snapshot_df["product_key"].map(product_id_by_key)

        long_df = snapshot_df.melt(
            id_vars=["product_id"],
            value_vars=LOCATION_QUANTITY_COLUMNS,
            var_name="quantity_column",
            value_name="quantity",
        )
        long_df["location_name"] = long_df["quantity_column"].str.replace(
            " Quantity", "", regex=False
        )
        long_df["quantity"] = long_df["quantity"].fillna(0)

        location_rows = conn.execute(
            text("SELECT location_id, location_name FROM locations")
        ).fetchall()
        location_id_by_name = {name: loc_id for loc_id, name in location_rows}

        deleted = conn.execute(
            text(
                "DELETE FROM inventory_snapshots WHERE snapshot_date = :snapshot_date"
            ),
            {"snapshot_date": snapshot_date},
        )
        print(f"Removed {deleted.rowcount} existing snapshot rows for {snapshot_date}")

        snapshot_rows = []
        for _, snap_row in long_df.iterrows():
            product_id = snap_row["product_id"]
            if pd.isna(product_id):
                continue

            location_name = snap_row["location_name"]
            location_id = location_id_by_name.get(location_name)
            if location_id is None:
                raise ValueError(f"Unknown location: {location_name}")

            snapshot_rows.append(
                {
                    "snapshot_date": snapshot_date,
                    "product_id": int(product_id),
                    "location_id": location_id,
                    "quantity": float(snap_row["quantity"]),
                }
            )

        snapshot_count = len(snapshot_rows)
        for i in range(0, snapshot_count, SNAPSHOT_CHUNK_SIZE):
            chunk = snapshot_rows[i : i + SNAPSHOT_CHUNK_SIZE]
            conn.execute(SNAPSHOT_INSERT, chunk)

        print(f"Inserted {snapshot_count} inventory snapshot rows")


if __name__ == "__main__":
    excel_files = sorted(raw_dir.glob("*.xlsx"))
    if not excel_files:
        raise FileNotFoundError(f"No .xlsx files found in {raw_dir}")

    import_file(excel_files[0])
    print("Import complete.")
