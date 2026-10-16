import re
import unicodedata


def clean_text(value):
    """Trim whitespace and collapse repeated spaces; blank input becomes None."""
    if value is None:
        return None
    value = unicodedata.normalize("NFKC", str(value)).strip()
    value = re.sub(r"\s+", " ", value)
    return value or None


def normalize_name(value):
    value = clean_text(value)
    if not value:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^A-Za-z0-9 ]+", " ", value).lower()
    return re.sub(r"\s+", " ", value).strip() or None


def normalize_email(value):
    value = clean_text(value)
    return value.lower() if value else None


def normalize_phone(value):
    value = clean_text(value)
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    # Normalize Indian +91 numbers to their national 10-digit form.
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    # Do not treat short fragments as a reliable phone identifier.
    return digits if len(digits) >= 10 else None


def normalize_postal_code(value):
    value = clean_text(value)
    return re.sub(r"\s+", "", value).upper() if value else None


def normalize_city(value):
    value = clean_text(value)
    return value.lower() if value else None


def normalize_record(record):
    """Return a copy with consistent display values and normalized match keys."""
    row = {key: clean_text(value) for key, value in record.items()}
    row["customer_id"] = clean_text(row.get("customer_id"))
    row["source"] = clean_text(row.get("source")) or "unknown"
    row["name"] = clean_text(row.get("name"))
    row["email"] = normalize_email(row.get("email"))
    row["phone"] = normalize_phone(row.get("phone"))
    row["city"] = clean_text(row.get("city"))
    row["postal_code"] = normalize_postal_code(row.get("postal_code"))
    row["_name_key"] = normalize_name(row.get("name"))
    row["_city_key"] = normalize_city(row.get("city"))
    return row
