from collections import defaultdict
from itertools import product

from .matching import compare_records
from .normalization import normalize_record


FIELDS = ["name", "email", "phone", "city", "postal_code"]


class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item):
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left, right):
        left_root, right_root = self.find(left), self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def _record_key(record):
    return (record.get("source"), record.get("customer_id"))


def resolve_customers(source_a, source_b, explainer=None):
    """
    Normalize two source datasets, compare cross-source pairs, and build golden records.
    Only 'match' decisions are merged. 'review' decisions remain separate.
    """
    explainer = explainer or _DefaultExplainer()
    records = [normalize_record(row) for row in source_a + source_b]
    left_count = len(source_a)
    uf = UnionFind(len(records))
    decisions = []

    for left_index, right_index in product(range(left_count), range(left_count, len(records))):
        left, right = records[left_index], records[right_index]
        result = compare_records(left, right)
        decision = {
            "left_source": left.get("source"),
            "left_customer_id": left.get("customer_id"),
            "right_source": right.get("source"),
            "right_customer_id": right.get("customer_id"),
            **result,
        }
        decision["explanation"] = explainer.explain(decision)
        decisions.append(decision)
        if result["decision"] == "match":
            uf.union(left_index, right_index)

    clusters = defaultdict(list)
    for index, record in enumerate(records):
        clusters[uf.find(index)].append(record)

    golden_records = []
    for members in clusters.values():
        # CRM wins ties by being first in this explicit source-priority list.
        members = sorted(members, key=lambda r: (0 if r.get("source") == "crm" else 1,
                                                  str(r.get("customer_id") or "")))
        merged = {}
        for field in FIELDS:
            merged[field] = next((member.get(field) for member in members if member.get(field)), None)
        source_refs = [
            {"source": member.get("source"), "customer_id": member.get("customer_id")}
            for member in members
        ]
        golden_id = "GR-" + "-".join(
            f"{ref['source']}-{ref['customer_id']}" for ref in source_refs
        )
        golden_records.append({
            "golden_id": golden_id,
            **merged,
            "source_count": len(members),
            "source_records": source_refs,
        })

    golden_records.sort(key=lambda row: row["golden_id"])
    return records, golden_records, decisions


class _DefaultExplainer:
    def explain(self, decision):
        return decision["explanation"]
