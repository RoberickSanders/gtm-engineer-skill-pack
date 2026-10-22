"""10-sample-row approval gate shared by every skill."""
import csv, json, os, sys

SAMPLE_SIZE = 10

def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def require(rows, cols):
    if not rows:
        sys.exit("ERROR: input has no rows")
    missing = [c for c in cols if c not in rows[0]]
    if missing:
        sys.exit(f"ERROR: missing required column(s): {', '.join(missing)}")

def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def run_gated(skill, rows, process, approve, out_root="out", summarize=None):
    """Process 10 rows, stop unless approved, then process all rows."""
    out = os.path.join(out_root, skill)
    sample = process(rows[:SAMPLE_SIZE])
    write_csv(os.path.join(out, "sample.csv"), sample)
    print(f"[{skill}] SAMPLE ({len(sample)} rows) -> {out}/sample.csv")
    for r in sample:
        print("  ", {k: r[k] for k in list(r)[:6]})
    if not approve:
        print(f"[{skill}] GATE: review the sample, then re-run with --approve for all {len(rows)} rows.")
        return None
    full = process(rows)
    write_csv(os.path.join(out, "full.csv"), full)
    summary = {"skill": skill, "input_rows": len(rows), "output_rows": len(full)}
    if summarize:
        summary.update(summarize(full))
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[{skill}] FULL -> {out}/full.csv  summary: {summary}")
    return full
