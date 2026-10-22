"""Job 2: qualify each account (AI stand-in) before paying to enrich it."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from gtm.gate import read_csv, require, run_gated
from gtm.cli import parser

POSITIVE = ["paid social", "google ads", "meta", "roas", "agency", "brands", "online store", "marketing analyst"]
NEGATIVE = ["student", "blog", "bakery", "hospital"]

def classify(row):
    """Offline stand-in for one batched LLM call. Returns (fit, confidence, reason).
    Swap this function for a real model call; keep the same return shape."""
    text = f"{row.get('website_note','')} {row.get('industry','')}".lower()
    pos = [k for k in POSITIVE if k in text]
    neg = [k for k in NEGATIVE if k in text]
    if neg:
        return "no", 0.9, f"disqualifier: {', '.join(neg)}"
    if pos:
        return "yes", min(0.6 + 0.1 * len(pos), 0.95), f"evidence: {', '.join(pos)}"
    return "unsure", 0.4, "no evidence either way"

def process(rows):
    out = []
    for r in rows:
        fit, conf, why = classify(r)
        out.append({**r, "fit": fit, "fit_confidence": round(conf, 2), "fit_reason": why,
                    "send_to_enrichment": "yes" if fit == "yes" and conf >= 0.7 else "no"})
    return out

def summarize(full):
    kept = sum(r["send_to_enrichment"] == "yes" for r in full)
    return {"qualified": kept, "paid_lookups_avoided": len(full) - kept}

if __name__ == "__main__":
    a = parser(__doc__).parse_args()
    rows = read_csv(a.input)
    require(rows, ["domain", "industry", "website_note"])
    run_gated("02-qualify-before-enrich", rows, process, a.approve, a.out, summarize)
