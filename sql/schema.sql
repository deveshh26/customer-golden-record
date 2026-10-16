PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_customer (
    source_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    customer_id TEXT,
    name TEXT,
    email TEXT,
    phone TEXT,
    city TEXT,
    postal_code TEXT,
    raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS golden_customer (
    golden_id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT,
    phone TEXT,
    city TEXT,
    postal_code TEXT,
    source_count INTEGER NOT NULL CHECK (source_count >= 1),
    source_records_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS match_decision (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    left_source TEXT NOT NULL,
    left_customer_id TEXT,
    right_source TEXT NOT NULL,
    right_customer_id TEXT,
    decision TEXT NOT NULL CHECK (decision IN ('match', 'review', 'no_match')),
    rule TEXT NOT NULL,
    name_similarity REAL NOT NULL CHECK (name_similarity >= 0 AND name_similarity <= 1),
    explanation TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_customer_email ON source_customer(email);
CREATE INDEX IF NOT EXISTS idx_source_customer_phone ON source_customer(phone);
CREATE INDEX IF NOT EXISTS idx_match_decision_type ON match_decision(decision);
