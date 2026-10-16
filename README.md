# Customer Golden Record

A small, runnable customer identity-resolution project that combines two messy customer datasets, standardizes key fields, identifies likely duplicates, creates golden records, and writes an auditable explanation for every cross-source comparison.

## What it does

1. Reads synthetic CRM and billing CSV files.
2. Normalizes names, email addresses, phone numbers, city values, and postal codes.
3. Compares each CRM record against each billing record using deterministic rules and fuzzy name similarity.
4. Labels each pair `match`, `review`, or `no_match`.
5. Merges only `match` pairs into golden records. Review candidates are intentionally **not** auto-merged.
6. Writes CSV, JSON, JSONL, and SQLite outputs.

## Matching rules

| Rule | Outcome | Reason |
|---|---|---|
| Exact normalized email | Match | Strong identifier |
| Exact normalized phone (10+ digits) | Match | Strong identifier |
| Name similarity >= 0.92 and same non-empty postal code | Match | Fuzzy name plus location corroboration |
| Name similarity >= 0.86 and same postal code or city | Review | Plausible but not safe enough to auto-merge |
| Everything else | No match | Evidence is insufficient |

Name similarity uses Python's standard-library `difflib.SequenceMatcher`. It is deterministic and has no external service dependency. These thresholds are demo defaults, not universal production thresholds.

### Golden record policy

For a matched cluster, non-empty values are selected field-by-field using source priority: CRM first, then billing. The output preserves source references and a source count for traceability. The demo uses connected components for exact/fuzzy match links; as with any transitive clustering approach, production use should add cluster-level contradiction checks and human review.

## Requirements

- Python 3.10+
- No third-party runtime packages
- SQLite (included with supported Python distributions)
- Optional: local Ollama install and a model downloaded locally, only if you choose the Ollama explanation adapter



## Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/deveshh26/customer-golden-record.git
cd customer-golden-record
```

Create and activate a virtual environment.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the project:

```bash
python -m pip install -e .
```

No API keys or secrets are needed.

## Run

Run the pipeline:

```bash
customer-golden-record
```

Or run without installing the command entry point:

```bash
PYTHONPATH=src python -m golden_record.cli
```

To provide different CSV files:

```bash
customer-golden-record --crm data/customers_crm.csv --billing data/customers_billing.csv --output outputs
```

The CSV input headers should be `customer_id,name,email,phone,city,postal_code`. Source names are assigned by the CLI (`crm` and `billing`).


## Output files

- `outputs/golden_records.csv` — standardized golden records.
- `outputs/golden_records.json` — structured golden records.
- `outputs/match_decisions.csv` — pair decisions with rule, similarity, and explanation.
- `outputs/match_decisions.jsonl` — one JSON object per comparison, convenient for AI or log ingestion.
- `outputs/golden_record.db` — SQLite database with source records, golden records, and match decisions.

## SQL model

The schema is in `sql/schema.sql`. It contains:
- `source_customer`: normalized source rows plus a raw JSON snapshot.
- `golden_customer`: one record per resolved identity, with source references.
- `match_decision`: an audit table with rule, decision, similarity, and explanation.

Example query:

```sql
SELECT decision, COUNT(*) AS pair_count
FROM match_decision
GROUP BY decision
ORDER BY decision;
```

## Explanation provider / AI boundary

Explanations are isolated behind `ExplanationProvider` in `src/golden_record/explainers.py`.

- Default `rules`: deterministic local explanations; no AI call or network access.
- Optional `ollama`: sends only structured decision evidence (decision, rule, similarity, existing evidence explanation) to a local Ollama endpoint. It is not enabled by default and does not decide whether two records match. Matching decisions remain deterministic.

To use the optional local model, start Ollama, pull a model such as `llama3.2`, then run:

```bash
customer-golden-record --explainer ollama
```

If the local model is unavailable, the run fails clearly rather than silently pretending an AI call succeeded. No secrets are embedded in source code.

## Tests and edge case

```bash
python -m unittest discover -s tests -v
```

Tests cover normalized exact-email matches, fuzzy name matching with postal-code corroboration, missing identifiers with conflicting locations, transitive cluster behavior, and empty input. The missing-identifier test is the failure/edge-case demonstration: two records share a name but have different cities/postal codes and are not auto-merged.

## Architecture

```text
CRM CSV ─┐
         ├─> normalization ─> cross-source matching ─> match decisions
Billing ─┘                                       └─> golden record clusters
                                                      ├─ CSV / JSON / JSONL
                                                      └─ SQLite SQL model

Match decision ─> ExplanationProvider
                   ├─ rules (default)
                   └─ Ollama (optional local model)
```

## Demo video plan (5–8 minutes)

1. **0:00–0:45** — State the problem: duplicate customer records across CRM and billing.
2. **0:45–1:30** — Show the two synthetic CSVs and the messy differences.
3. **1:30–2:30** — Explain normalization and the exact/fuzzy matching rules.
4. **2:30–3:30** — Run `customer-golden-record` and inspect the generated golden records.
5. **3:30–4:30** — Open `match_decisions.csv` or `.jsonl` and show readable evidence.
6. **4:30–5:30** — Query `outputs/golden_record.db` using the SQL example.
7. **5:30–6:30** — Run the tests and explain the missing-identifier edge case.
8. **6:30–7:00** — Close with tradeoffs and next steps: blocking for scale, calibrated thresholds, cluster conflict checks, and review workflow.

## Limitations and next steps

- Pairwise comparison is O(N × M), suitable for a small demo, not very large datasets.
- `SequenceMatcher` is a simple baseline, not a specialized entity-resolution model.
- Shared email/phone can be stale or household-level; production systems should assess identifier reliability.
- Connected components can propagate a mistaken link. Add cluster-level conflict checks and human review before using for business-critical merges.
- Golden field selection uses a fixed CRM-first source priority. Production should use field-level trust, recency, and provenance.
- This project uses synthetic data only.
