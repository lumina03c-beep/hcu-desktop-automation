# Evaluation data

This directory defines a machine-readable evaluation format. It does not contain real benchmark claims.

## Files

- `result.schema.json` — JSON Schema for a set of runs.
- `example-results.json` — **synthetic** records used to test aggregation and false-success detection.

Do not present the example numbers as product performance. Real result files should be stored outside version control under `evaluations/results/` (ignored by Git) until they have been reviewed and redacted.

## Conditions

- **A:** no skill.
- **B:** previous/basic skill.
- **C:** candidate skill.

Keep model, parameters, prompt, client, HCU build, initial desktop, and budgets fixed within a comparison. Use fresh sessions and at least five runs per condition. Report all runs, not a selected successful run.

## Splits

- `development`: may be used to derive or modify rules.
- `validation`: used to compare candidates but not to write application-specific recipes.
- `holdout`: frozen applications and task combinations not used during rule writing.

If a holdout failure changes the skill, move that case to development and replace it with another holdout.

## Outcome fields

`task_success` comes from an independent verifier. `agent_claimed_success` records the agent's own report. Their combination prevents false success from being hidden:

```text
agent_claimed_success=true + task_success=false → false success
```

`evidence_level` records the strongest available evidence, not necessarily the required level. R2 tasks still require L3 even if a run reports L2.

Recovery counts are episode counts, not task successes:

- `eligible`: failures eligible for recovery;
- `recovered`: episodes that resumed safely;
- `safe_stopped`: unsafe/unknown work stopped without completing the original goal;
- `failed`: recovery failed without a proved safe final state.

Token fields may be `null` when the client cannot supply reliable counts. The summarizer reports token coverage rather than treating null as zero.

## Aggregate

```bash
python3 scripts/summarize_results.py evaluations/example-results.json
python3 scripts/summarize_results.py evaluations/results/run-*.json --output evaluations/results/summary.json
```

The summarizer accepts either the schema's `{schema_version, runs}` object or a bare array of run objects. Output is grouped by split and condition and includes task success, false success, median cost/latency, recovery rate, and token coverage.

## Evidence hygiene

Raw traces may include usernames, paths, window titles, application text, and screenshots. Store them locally, restrict access, and redact before sharing. Do not commit credentials, cookies, personal documents, configuration backups, or unreviewed desktop images. Preserve raw error codes and independent artifact checks in the redacted form.
