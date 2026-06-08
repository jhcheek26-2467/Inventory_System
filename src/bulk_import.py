import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Allow `python src/bulk_import.py` from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_inventory import import_file, parse_filename

load_dotenv()

project_root = Path(__file__).resolve().parent.parent
raw_dir = project_root / "data" / "raw"

engine = create_engine(os.getenv("DATABASE_URL"))


def get_existing_snapshot_dates(conn):
    rows = conn.execute(
        text("SELECT DISTINCT snapshot_date FROM inventory_snapshots ORDER BY snapshot_date")
    ).fetchall()
    return {str(row[0]) for row in rows}


def pick_latest_file_per_date(excel_files):
    """
    Sort by date then timestamp; keep only the newest export for each date.
    Returns (files_to_import, skipped_duplicates) where skipped_duplicates is
    a list of (path, reason) for older same-day exports.
    """
    parsed_files = []
    unparseable = []

    for path in excel_files:
        parsed = parse_filename(path.name)
        if parsed is None:
            unparseable.append(path)
            continue
        snapshot_date, timestamp = parsed
        parsed_files.append((path, snapshot_date, timestamp))

    parsed_files.sort(key=lambda item: (item[1], item[2]))

    latest_by_date = {}
    for path, snapshot_date, timestamp in parsed_files:
        latest_by_date[snapshot_date] = path

    skipped_duplicates = []
    for path, snapshot_date, timestamp in parsed_files:
        if latest_by_date[snapshot_date] != path:
            skipped_duplicates.append(
                (
                    path,
                    f"not the latest export for {snapshot_date} (timestamp {timestamp})",
                )
            )

    files_to_import = [latest_by_date[date] for date in sorted(latest_by_date.keys())]
    return files_to_import, skipped_duplicates, unparseable


def main():
    excel_files = sorted(raw_dir.glob("*.xlsx"))
    if not excel_files:
        print(f"No .xlsx files found in {raw_dir}")
        return

    imported = []
    skipped = []
    failed = []

    files_to_import, skipped_duplicates, unparseable = pick_latest_file_per_date(
        excel_files
    )

    for path in unparseable:
        reason = "filename missing _Inventory_YYYY-MM-DD date pattern"
        skipped.append((path, reason))
        print(f"SKIP  {path.name}: {reason}")

    for path, reason in skipped_duplicates:
        skipped.append((path, reason))
        print(f"SKIP  {path.name}: {reason}")

    with engine.connect() as conn:
        existing_dates = get_existing_snapshot_dates(conn)

    for path in files_to_import:
        parsed = parse_filename(path.name)
        snapshot_date, _timestamp = parsed

        if snapshot_date in existing_dates:
            reason = f"snapshot date {snapshot_date} already in database"
            skipped.append((path, reason))
            print(f"SKIP  {path.name}: {reason}")
            continue

        try:
            import_file(path)
            imported.append(path)
            existing_dates.add(snapshot_date)
            print(f"OK    {path.name}")
        except Exception as exc:
            reason = str(exc)
            failed.append((path, reason))
            print(f"FAIL  {path.name}: {reason}")

    print()
    print("Summary")
    print(f"  Imported: {len(imported)}")
    print(f"  Skipped:  {len(skipped)}")
    print(f"  Failed:   {len(failed)}")

    if imported:
        print("\nImported files:")
        for path in imported:
            print(f"  - {path.name}")

    if failed:
        print("\nFailed files:")
        for path, reason in failed:
            print(f"  - {path.name}: {reason}")


if __name__ == "__main__":
    main()
