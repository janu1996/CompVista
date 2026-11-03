import csv
import json
import hashlib
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

from app import app
from extensions import db
from models import (
    Role, Level, Location, Employee,
    CompensationBand, FXRate, SalaryRecord,
    Promotion, PerformanceEvidence, Tenure
)

ROOT = Path(__file__).resolve().parent.parent

CSV_DIR = ROOT / "data" / "csv"
JSON_DIR = ROOT / "data" / "json"
SQL_DIR = ROOT / "data" / "sql"

for folder in (CSV_DIR, JSON_DIR, SQL_DIR):
    folder.mkdir(parents=True, exist_ok=True)

MODELS = [
    Role, Level, Location, Employee,
    CompensationBand, FXRate, SalaryRecord,
    Promotion, PerformanceEvidence, Tenure
]


def serialize(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def sql_value(value):
    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (int, float, Decimal)):
        return str(value)

    value = serialize(value)
    return "'" + str(value).replace("'", "''") + "'"


def main():
    manifest = {}

    with app.app_context():

        # Export CSV and JSON
        for model in MODELS:
            table = model.__tablename__

            records = model.query.order_by(
                *list(model.__table__.primary_key.columns)
            ).all()

            columns = [
                column.name for column in model.__table__.columns
            ]

            rows = [
                {
                    column: serialize(getattr(record, column))
                    for column in columns
                }
                for record in records
            ]

            csv_path = CSV_DIR / f"{table}.csv"
            json_path = JSON_DIR / f"{table}.json"

            with csv_path.open(
                "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(
                    file, fieldnames=columns
                )
                writer.writeheader()
                writer.writerows(rows)

            with json_path.open(
                "w", encoding="utf-8"
            ) as file:
                json.dump(rows, file, indent=2)

            manifest[table] = {
                "records": len(rows),
                "csv": f"data/csv/{table}.csv",
                "json": f"data/json/{table}.json"
            }

            print(f"{table}: {len(rows)} records exported")

        # Export SQL INSERT statements
        sql_path = SQL_DIR / "compvista_seed.sql"

        with sql_path.open(
            "w", encoding="utf-8"
        ) as file:

            file.write("-- CompVista synthetic dataset export\n")
            file.write("-- Create the database schema before importing.\n\n")
            file.write("PRAGMA foreign_keys = ON;\n")
            file.write("BEGIN TRANSACTION;\n\n")

            for model in MODELS:
                table = model.__tablename__

                columns = [
                    column.name
                    for column in model.__table__.columns
                ]

                records = model.query.order_by(
                    *list(model.__table__.primary_key.columns)
                ).all()

                for record in records:
                    values = [
                        sql_value(getattr(record, column))
                        for column in columns
                    ]

                    file.write(
                        f"INSERT INTO {table} "
                        f"({', '.join(columns)}) VALUES "
                        f"({', '.join(values)});\n"
                    )

                file.write("\n")

            file.write("COMMIT;\n")

        # Calculate checksum for all exported files
        checksum = hashlib.sha256()

        for folder in (CSV_DIR, JSON_DIR, SQL_DIR):
            for path in sorted(folder.glob("*")):
                if path.is_file() and not path.name.startswith("ground_truth"):
                    checksum.update(
                        path.relative_to(ROOT).as_posix().encode()
                    )
                    checksum.update(path.read_bytes())

        manifest["sha256"] = checksum.hexdigest()

        with (ROOT / "data" / "export_manifest.json").open(
            "w", encoding="utf-8"
        ) as file:
            json.dump(manifest, file, indent=2)

        print("\nSQL export:", sql_path)
        print("SHA256:", manifest["sha256"])
        print("EXPORT COMPLETED")


if __name__ == "__main__":
    main()