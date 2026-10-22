"""Job 1: score every account with a transparent points model."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from gtm.gate import read_csv, require, run_gated
from gtm.cli import parser

ICP_INDUSTRIES = {"Marketing Agency": 30, "E-commerce": 20, "SaaS": 20, "Retail": 15, "Fintech": 10}
GEO = {"US": 10, "CA": 8, "UK": 8}

def score(row):
    pts, why = 0, []
    p = ICP_INDUSTRIES.get(row["industry"], 0)
    if p: pts += p; why.append(f"industry +{p}")
    emp = int(row["employees"] or 0)
    p = 25 if 100 <= emp <= 2000 else 15 if 2000 < emp <= 10000 else 5 if emp >= 30 else 0
    if p: pts += p; why.append(f"size {emp} +{p}")
    p = GEO.get(row["country"], 0)
    if p: pts += p; why.append(f"geo +{p}")
    roles = int(row.get("open_roles") or 0)
    p = min(roles, 10) * 2
    if p: pts += p; why.append(f"hiring {roles} roles +{p}")
    if row.get("raised_last_12mo") == "yes": pts += 15; why.append("raised +15")
    tier = "A" if pts >= 70 else "B" if pts >= 45 else "C"
    return {**row, "score": pts, "tier": tier, "score_reasons": "; ".join(why)}

def process(rows):
    return sorted((score(r) for r in rows), key=lambda r: -r["score"])

if __name__ == "__main__":
    a = parser(__doc__).parse_args()
    rows = read_csv(a.input)
    require(rows, ["domain", "industry", "employees", "country"])
    run_gated("01-map-and-score-market", rows, process, a.approve, a.out,
              lambda full: {t: sum(r["tier"] == t for r in full) for t in "ABC"})
