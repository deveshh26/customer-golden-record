import csv
import json
import sqlite3
from pathlib import Path


def read_csv(path, source_name):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            row["source"] = source_name
            rows.append(row)
    return rows


def write_csv(path, rows, fields):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def save_database(path, records, golden_records, pair_decisions):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        schema_path = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        for row in records:
            connection.execute(
                """INSERT INTO source_customer
                (source, customer_id, name, email, phone, city, postal_code, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (row.get("source"), row.get("customer_id"), row.get("name"),
                 row.get("email"), row.get("phone"), row.get("city"),
                 row.get("postal_code"), json.dumps(row, ensure_ascii=False)),
            )
        for row in golden_records:
            connection.execute(
                """INSERT INTO golden_customer
                (golden_id, name, email, phone, city, postal_code, source_count, source_records_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (row["golden_id"], row.get("name"), row.get("email"), row.get("phone"),
                 row.get("city"), row.get("postal_code"), row["source_count"],
                 json.dumps(row["source_records"], ensure_ascii=False)),
            )
        for row in pair_decisions:
            connection.execute(
                """INSERT INTO match_decision
                (left_source, left_customer_id, right_source, right_customer_id,
                 decision, rule, name_similarity, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (row["left_source"], row["left_customer_id"], row["right_source"],
                 row["right_customer_id"], row["decision"], row["rule"],
                 row["name_similarity"], row["explanation"]),
            )
        connection.commit()
    finally:
        connection.close()
