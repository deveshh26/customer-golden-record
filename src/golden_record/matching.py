from difflib import SequenceMatcher


def name_similarity(left, right):
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def compare_records(left, right):
    """
    Compare two records from different source systems.
    Decisions are deterministic and include a human-readable audit explanation.
    """
    evidence = []
    score = name_similarity(left.get("_name_key"), right.get("_name_key"))

    if left.get("email") and right.get("email") and left["email"] == right["email"]:
        return {
            "decision": "match",
            "rule": "exact_email",
            "name_similarity": round(score, 3),
            "explanation": "Matched on the same normalized email address.",
        }

    if left.get("phone") and right.get("phone") and left["phone"] == right["phone"]:
        return {
            "decision": "match",
            "rule": "exact_phone",
            "name_similarity": round(score, 3),
            "explanation": "Matched on the same normalized phone number.",
        }

    same_postal = bool(left.get("postal_code") and right.get("postal_code")
                       and left["postal_code"] == right["postal_code"])
    same_city = bool(left.get("_city_key") and right.get("_city_key")
                     and left["_city_key"] == right["_city_key"])

    if score >= 0.92 and same_postal:
        return {
            "decision": "match",
            "rule": "fuzzy_name_postal",
            "name_similarity": round(score, 3),
            "explanation": (
                f"Matched on a similar normalized name (similarity {score:.3f}) "
                "and the same postal code."
            ),
        }

    if score >= 0.86 and (same_postal or same_city):
        evidence.append("similar name and matching location")
        decision = "review"
        explanation = (
            f"Possible match: name similarity is {score:.3f} and a location field "
            "matches. Review manually; this pair is not auto-merged."
        )
        rule = "review_name_location"
    else:
        decision = "no_match"
        rule = "insufficient_evidence"
        explanation = (
            f"No automatic match: name similarity is {score:.3f}; "
            "no strong identifier rule was satisfied."
        )

    return {
        "decision": decision,
        "rule": rule,
        "name_similarity": round(score, 3),
        "explanation": explanation,
    }
