"""Check the agents' "finalized" claims against the transactions table.

Run it right after run_test_scenarios() has produced test_results.csv.
init_database() rebuilds munder_difflin.db on every run, so the CSV and the
database must come from the same run.

Usage:
    python reconcile.py [test_results.csv] [munder_difflin.db]

For every response it finds the transaction IDs the agents quoted, looks each
one up in the database, and reports whether the ID exists, whether it is a
sale, and whether the price in the database appears in the response text.
"""
import re
import sqlite3
import sys

import pandas as pd

results_path = sys.argv[1] if len(sys.argv) > 1 else "test_results.csv"
db_path = sys.argv[2] if len(sys.argv) > 2 else "munder_difflin.db"

ID_PATTERN = re.compile(r"transaction\s*ids?", re.IGNORECASE)
NUMBER = re.compile(r"(?<![\w$.,])(\d{1,6})(?![\w]|[.,]\d)")


def claimed_ids(text: str) -> list:
    """Integers after the words 'transaction id', up to the end of that sentence (prices and names like A4 are skipped)."""
    ids = []
    for line in text.splitlines():
        for m in ID_PATTERN.finditer(line):
            segment = re.split(r"\.(?=\s|$)", line[m.end():])[0]  # stop at the end of the sentence
            ids += [int(n.group(1)) for n in NUMBER.finditer(segment)]
    return sorted(set(ids))


def price_in_text(price: float, text: str) -> bool:
    forms = {f"{price:.2f}", f"{price:,.2f}", f"{price:.0f}" if price == int(price) else ""}
    return any(f and f in text for f in forms)


conn = sqlite3.connect(db_path)
tx = pd.read_sql("SELECT * FROM transactions", conn).set_index("id")
results = pd.read_csv(results_path)

rows, mentioned = [], set()
for _, r in results.iterrows():
    text = str(r["response"])
    ids = claimed_ids(text)
    positive = bool(ids) or bool(re.search(r"finaliz|fulfill|successful", text, re.IGNORECASE))
    negative = bool(re.search(r"(unable|cannot|could not|rejected|not be (?:finalized|fulfilled))", text, re.IGNORECASE))
    claims_success = positive and not (negative and not ids)
    if not ids:
        rows.append((r["request_id"], r["request_date"], claims_success, None, "no transaction id quoted", "", ""))
        continue
    for i in ids:
        mentioned.add(i)
        if i not in tx.index:
            rows.append((r["request_id"], r["request_date"], claims_success, i, "ID NOT IN DATABASE", "", ""))
            continue
        t = tx.loc[i]
        status = "ok" if t["transaction_type"] == "sales" else f"is a {t['transaction_type']}, not a sale"
        rows.append((
            r["request_id"], r["request_date"], claims_success, i, status,
            f"{t['item_name']} x{t['units']} ${t['price']:.2f} dated {str(t['transaction_date'])[:10]}",
            "yes" if price_in_text(float(t["price"]), text) else "no",
        ))

out = pd.DataFrame(rows, columns=["request_id", "request_date", "claims_success", "tx_id", "check", "db_record", "price_in_response"])
out["tx_id"] = out["tx_id"].astype("Int64")
pd.set_option("display.width", 220, "display.max_colwidth", 70)
print(out.to_string(index=False))

unsupported = out[(out["claims_success"]) & (out["check"] != "ok")]
print(f"\nResponses claiming success: {int(out.groupby('request_id')['claims_success'].max().sum())}")
print(f"Success claims with a missing or invalid transaction id: {unsupported['request_id'].nunique()}")
sales_not_mentioned = tx[(tx["transaction_type"] == "sales") & (tx["item_name"].notna()) & (~tx.index.isin(mentioned))]
print(f"Sales rows in the database that no response mentions: {len(sales_not_mentioned)}")
