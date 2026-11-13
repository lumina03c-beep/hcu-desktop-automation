# Evaluation data

This directory defines a machine-readable evaluation format. It does not contain real benchmark claims.

## Files

- `v2/result.schema.json` — **primary** JSON Schema for one evaluation run (per-run record).
- `v2/example-results.json` — **synthetic** V2 records used to test aggregation and false-success detection.
- `v2/example-metrics.json` — runtime-only metrics fixture for the bundled Workspace example.
- `result.schema.json` — deprecated V1 schema, kept to read historical data; do not add fields.
- `example-results.json` — **synthetic** V1 records for backward-compatibility tests.

Do not present the example numbers as product performance. Real result files should be stored outside version control under `evaluations/results/` (ignored by Git) until they have been reviewed and redacted.

## Pipeline

```text
Workspace (events/handoffs) → scripts/workspace_metrics.py (coverage-aware metrics)
    → scripts/workspace_to_v2.py (requires --verified + --verifier + --metrics-file)
    → evaluations/v2/result.schema.json record
    → scripts/summarize_results.py (grouped by split and condition)
```

`scripts/summarize_results.py` auto-detects the record schema: V2
(`schema_version: "2.0.0"`) is the primary path; V1 records remain readable
and are reported with `record_schema: "v1"`. Never mix V1 and V2 records in
one batch.

To turn a Workspace into a V2 record:

```bash
python3 scripts/workspace_to_v2.py <workspace.json> \
  --case-id <case> --verified true --verifier <verifier-id> \
  --platform windows --client <client-id> --model <model-id> \
  --metrics-file <runtime-metrics.json>
```

The adapter refuses to run without an independent verification verdict: the
Workspace claim (`result.status`) is recorded only as
`agent_claimed_success`, and `task_success` comes solely from `--verified`.
Runtime-only metrics that a Workspace cannot derive (snapshots, AX/GUI calls,
duplicate mutations) must be supplied via `--metrics-file`; missing fields
are reported, never invented as zero.

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
python3 scripts/summarize_results.py evaluations/v2/example-results.json
python3 scripts/summarize_results.py evaluations/example-results.json
python3 scripts/summarize_results.py evaluations/results/run-*.json --output evaluations/results/summary.json
```

The summarizer accepts either the schema's `{schema_version, runs}` object or a bare array of run objects. Output is grouped by split and condition and includes task success, false success, median cost/latency with P90, recovery rates (recovered/safe_stopped/failed separate), and token coverage.

## Evidence hygiene

Raw traces may include usernames, paths, window titles, application text, and screenshots. Store them locally, restrict access, and redact before sharing. Do not commit credentials, cookies, personal documents, configuration backups, or unreviewed desktop images. Preserve raw error codes and independent artifact checks in the redacted form.
