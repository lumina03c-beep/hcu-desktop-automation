# Execution policy

Modes are chosen per step and never override the risk policy.

## Batch mode

Use when the target is identified, the UI state is stable, actions are
deterministic, the result is predictable, and risk is `R0` or low `R1`.

- Observe once, run one consecutive action batch, verify the terminal state.
- Browser: combine navigation, waits, actions, and the final observation in one
  script when safe. Desktop: obey HCU same-window and platform limits.
- Split at navigation, dynamic branches, and evidence-dependent decisions; a
  batch is not an unbounded mega-script.

## Adaptive mode

Use when the page or window is dynamic, the next action depends on the observed
result, popups or async loading may change the target, or the task branches.

- Observe → decide → execute → observe the needed change → update the plan.
- Re-plan only the affected local steps; never regenerate the whole task.
- Re-observe after page replacement, window change, or an uncertain effect.

## Critical mode

Use for delete, overwrite, submit, publish, send, purchase, permission changes,
and any `R2` action.

- Confirm the exact target and payload, obtain required approval, execute in
  isolation, and verify with independent `L3` evidence.
- Never hide a critical action inside an ordinary batch.

## Observation budget

- Each stage gets one orientation observation; after that read only the fields
  the next decision or success oracle needs.
- Prefer a targeted read (`evaluate` of fixed fields, `find`, `read`, one zoomed
  region) over a full snapshot or tree once the layout is known.
- One surface is enough; do not prove the same state through a snapshot, a
  screenshot, and a readback.
- Reuse stored semantic facts instead of re-observing unchanged state.
- Update the Workspace only at meaningful nodes; never persist reasoning, raw
  DOM, full AX trees, or unrelated screenshots.

## Model and round-trip economy

- Plan at stage level, not per action; batch stable actions into one script.
- One script or batch should cover navigate → act → wait for the terminal
  condition → targeted verification, and print only the terminal evidence.
- Set a soft round-trip budget per stage; when exceeded, change mechanism,
  channel, or engine instead of retrying the same shape.
- Move bulk content through an auxiliary channel (clipboard, file write) and
  keep delivery and verification in the UI engine.
- Return only decision-relevant results; never trade verification, safety, or
  `R2` isolation for fewer calls.
- Combine independent auxiliary operations (preflight, clipboard, readback
  hashing) into one script that prints per-step results.

## Telemetry

- Record compact `events` at stage boundaries: engine, kind, round trips,
  outcome, and tokens only when known.
- Derive the V2 metrics with `scripts/workspace_metrics.py`; leave unknown
  telemetry `null` and never estimate it into a success claim.
- Never store prompts, raw observations, screenshots, or payloads as telemetry.
