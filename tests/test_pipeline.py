import unittest

from golden_record.matching import compare_records
from golden_record.normalization import normalize_record
from golden_record.pipeline import resolve_customers


def row(source, customer_id, name="", email="", phone="", city="", postal_code=""):
    return {
        "source": source, "customer_id": customer_id, "name": name,
        "email": email, "phone": phone, "city": city, "postal_code": postal_code,
    }


class GoldenRecordTests(unittest.TestCase):
    def test_email_match_ignores_case_and_spaces(self):
        left = normalize_record(row("crm", "1", "Asha Sharma", " ASHA@EXAMPLE.COM "))
        right = normalize_record(row("billing", "2", "Different Name", "asha@example.com"))
        result = compare_records(left, right)
        self.assertEqual(result["decision"], "match")
        self.assertEqual(result["rule"], "exact_email")

    def test_fuzzy_name_requires_same_postal_code(self):
        left = normalize_record(row("crm", "1", "Jon Smyth", "", "", "Delhi", "110001"))
        right = normalize_record(row("billing", "2", "John Smyth", "", "", "Delhi", "110001"))
        self.assertEqual(compare_records(left, right)["rule"], "fuzzy_name_postal")
        right["postal_code"] = "400001"
        right["_city_key"] = "mumbai"
        self.assertEqual(compare_records(left, right)["decision"], "no_match")

    def test_missing_identifiers_do_not_force_match(self):
        left = normalize_record(row("crm", "1", "Jordan Lee", "", "", "Pune", "411001"))
        right = normalize_record(row("billing", "2", "Jordan Lee", "", "", "Mumbai", "400001"))
        result = compare_records(left, right)
        self.assertEqual(result["decision"], "no_match")

    def test_duplicate_rows_do_not_duplicate_identity_merge(self):
        a = [row("crm", "1", "Asha Sharma", "asha@example.com"),
             row("crm", "2", "Asha Sharma", "asha@example.com")]
        b = [row("billing", "3", "Asha Sharma", "asha@example.com")]
        _, golden, _ = resolve_customers(a, b)
        # Source duplicates are not deduplicated within one source; each can match across source.
        # This check makes the current transitive-clustering behavior explicit.
        self.assertEqual(len(golden), 1)
        self.assertEqual(golden[0]["source_count"], 3)

    def test_empty_sources_are_supported(self):
        _, golden, decisions = resolve_customers([], [])
        self.assertEqual(golden, [])
        self.assertEqual(decisions, [])


if __name__ == "__main__":
    unittest.main()
