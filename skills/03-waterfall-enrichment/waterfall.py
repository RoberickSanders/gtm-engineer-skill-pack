"""Job 3: free-before-paid enrichment waterfall with MOCK providers."""
import hashlib, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from gtm.gate import read_csv, require, run_gated
from gtm.cli import parser

def _h(s):  # deterministic pseudo-random 0-99 so runs are repeatable
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) % 100

def pattern_cache(row):   # free: known pattern for the domain
    first, last = row["contact_name"].lower().split()[:2]
    return f"{first}.{last}@{row['domain']}" if _h("cache" + row["domain"]) < 35 else None

def site_scrape(row):     # free: email published on the site (mocked)
    first = row["contact_name"].lower().split()[0]
    return f"{first}@{row['domain']}" if _h("site" + row["domain"]) < 30 else None

def mock_paid_a(row):
    first, last = row["contact_name"].lower().split()[:2]
    return f"{first[0]}{last}@{row['domain']}" if _h("a" + row["domain"]) < 55 else None

def mock_paid_b(row):
    first, last = row["contact_name"].lower().split()[:2]
    return f"{first}_{last}@{row['domain']}" if _h("b" + row["domain"]) < 50 else None

PROVIDERS = [("pattern_cache", 0.0, pattern_cache), ("site_scrape", 0.0, site_scrape),
             ("mock_paid_a", 0.01, mock_paid_a), ("mock_paid_b", 0.03, mock_paid_b)]

def verify(email):  # mock verifier: rejects a deterministic slice
    return email is not None and _h("v" + email) >= 10

def enrich(row):
    cost, tried = 0.0, []
    for name, price, fn in PROVIDERS:
        cost += price
        tried.append(name)
        email = fn(row)
        if email and verify(email):
            return {**row, "email": email, "provider": name, "providers_tried": ">".join(tried), "mock_cost": round(cost, 3)}
    return {**row, "email": "", "provider": "none", "providers_tried": ">".join(tried), "mock_cost": round(cost, 3)}

def process(rows):
    return [enrich(r) for r in rows if r.get("send_to_enrichment", "yes") == "yes"]

def summarize(full):
    found = sum(bool(r["email"]) for r in full)
    free = sum(r["provider"] in ("pattern_cache", "site_scrape") for r in full)
    return {"found": found, "coverage_pct": round(100 * found / max(len(full), 1), 1),
            "found_free": free, "total_mock_cost": round(sum(r["mock_cost"] for r in full), 3)}

if __name__ == "__main__":
    a = parser(__doc__).parse_args()
    rows = read_csv(a.input)
    require(rows, ["domain", "contact_name"])
    run_gated("03-waterfall-enrichment", rows, process, a.approve, a.out, summarize)
