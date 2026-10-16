import argparse
from pathlib import Path

from .explainers import get_explainer
from .pipeline import resolve_customers
from .storage import read_csv, save_database, write_csv, write_json, write_jsonl


def main():
    parser = argparse.ArgumentParser(description="Resolve customer records into golden records.")
    parser.add_argument("--crm", default="data/customers_crm.csv", help="CRM source CSV")
    parser.add_argument("--billing", default="data/customers_billing.csv", help="Billing source CSV")
    parser.add_argument("--output", default="outputs", help="Output directory")
    parser.add_argument("--explainer", choices=["rules", "ollama"], default="rules",
                        help="Explanation provider (default: local deterministic rules)")
    args = parser.parse_args()

    crm = read_csv(args.crm, "crm")
    billing = read_csv(args.billing, "billing")
    explainer = get_explainer(args.explainer)
    records, golden, decisions = resolve_customers(crm, billing, explainer)

    output = Path(args.output)
    write_csv(output / "golden_records.csv", golden, [
        "golden_id", "name", "email", "phone", "city", "postal_code",
        "source_count", "source_records"
    ])
    write_csv(output / "match_decisions.csv", decisions, [
        "left_source", "left_customer_id", "right_source", "right_customer_id",
        "decision", "rule", "name_similarity", "explanation"
    ])
    write_json(output / "golden_records.json", golden)
    write_jsonl(output / "match_decisions.jsonl", decisions)
    save_database(output / "golden_record.db", records, golden, decisions)

    counts = {label: sum(1 for row in decisions if row["decision"] == label)
              for label in ("match", "review", "no_match")}
    print(f"Source records: {len(records)}")
    print(f"Golden records: {len(golden)}")
    print(f"Pair decisions: {len(decisions)} ({counts})")
    print(f"Outputs written to: {output.resolve()}")


if __name__ == "__main__":
    main()
