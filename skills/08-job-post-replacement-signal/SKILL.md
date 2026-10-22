# Job Post Replacement Signal

> reads job posts to find who's hiring the role you replace

**Status:** Spec only

## One-message trigger
"Run job-post-replacement-signal on <client>/<list>." One message should be enough. The agent already has the client brief, ICP and market research loaded.

## Inputs
- Job post text per account
- Client brief (ICP, offer, exclusions)

## Steps
1. Load the input and validate the required columns. Stop on any missing column and say which one.
2. Run the job on the **first 10 rows only**.
3. Write `out/sample.csv` and print it.
4. **Gate:** stop and wait for a human to approve the 10 sample rows.
5. Only after approval, run the full list and write `out/full.csv` plus a run summary.

## The 10-sample-row gate
No full run, paid credit, send or CRM write happens until a person has looked at 10 real output rows and said yes. In code this means the script exits after the sample unless `--approve` is passed.

## Outputs
- `out/sample.csv` (10 rows, always)
- `out/full.csv` + `out/summary.json` (after approval only)

## Run
Spec only (no code in this pack yet).
