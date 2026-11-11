# Generalization and regression testing

Measure independently verified outcomes, not tool calls that returned `ok`.
Keep application recipes in the development set and prove generalization on
applications and task combinations never used to write rules.

## V2 evaluation

Record every run with `evaluations/v2/result.schema.json`.

| Metric | Definition |
| --- | --- |
| Task Completion Rate | verified completions / valid runs |
| False Success Rate | claimed success but independent verification fails / runs |
| Model Calls per Task | actual model decision calls; `null` if unknown |
| Tool Round Trips | Browser, Desktop, and auxiliary calls, reported separately |
| Observation Calls | Browser snapshots/screenshots; Desktop AX/GUI calls |
| Token Cost per Task | input and output tokens; `null` if unknown |
| End-to-End Latency | wall time from task start to verified terminal state |
| Handoff Latency | PREPARE start to the next engine confirmed ready |
| Recovery Rate | `recovered` / eligible failures; safe stops reported separately |
| Duplicate Mutation Rate | repeated external side effects / external mutations |

Workspace instrumentation maps to the same metrics: `events[]` supplies round
trips and recovery attempts, `handoffs[]` supplies handoff latency, and
`lifecycle` supplies end-to-end latency. `scripts/workspace_metrics.py` computes
per-task and aggregate values; missing telemetry stays `null`.

Rules:

- Compare A (original step-by-step) and B (V2 hybrid adaptive) under the same
  task, environment, model, permissions, budgets, and success oracle.
- Run each condition at least five times in fresh sessions.
- Keep development, regression, and frozen holdout cases separate; a holdout
  case that changes a rule is promoted to development and replaced.
- Mark synthetic runs explicitly; never mix them into real performance claims.
- Safe stops are reported separately and are not successes; `L3` verification
  is mandatory before claiming completion.
- If model-call or token telemetry is unavailable, record `null`; do not
  estimate it.

## Regression matrix

These 18 rows are development/regression coverage. A row that appears in
`scenarios.md` or motivated an existing rule cannot support a holdout claim.

| # | Task | Archetype | Expected route | Required evidence |
| --- | --- | --- | --- | --- |
| 1 | Open a site, search, play the first result | Browser | Direct URL if outcome-only; else UI | Playing state/title, not the click |
| 2 | Compute an expression in Calculator | Native UIA | AX find/click or set_value | Display value |
| 3 | Type a paragraph in Writer, save as .txt | Office | AX text + save dialog; file parse | File content on disk |
| 4 | Fill cells and a formula in Calc, save .csv | Office | AX cells; file parse | Parsed CSV values |
| 5 | Read, change, and restore a system toggle | Settings UI | AX find + state readback | Toggle state before/after |
| 6 | Create a folder and rename a file | File manager or shell | Shell preferred; UI only if required | Filesystem listing |
| 7 | Open two Notepad windows and enter different text | Multi-window | `apps`, `activate`, type per window | Each window title/content |
| 8 | Save As into a chosen folder | Dialog | AX fields/buttons; wait for dialog | File exists and content |
| 9 | Type Chinese/emoji text and save | Unicode input | AX/type; platform text path | File bytes/content |
| 10 | Draw a stroke in Paint and save | Canvas/GUI | Screenshot, drag path, screenshot | Saved image/pixels |
| 11 | Reach a playable video in Bilibili | Electron/empty AX | Detect early; GUI or web fallback | Playing state |
| 12 | Operate a GUI-only app | GUI-only | `apps` + GUI; AX for windows | Visible state change |
| 13 | Scroll a long page and open a located item | Scroll/list | `scroll`, `find`/text wait | Target page state |
| 14 | Zoom, map coordinates, and click a small control | GUI zoom | Screenshot -> zoom -> mapped point | Resulting state |
| 15 | Launch an app with a splash and act | Slow startup | Window wait, no stacked waits | Window inventory |
| 16 | Act while an unrelated window covers the target | Occlusion | Remove occluder or keyboard path | No repeated point failures |
| 17 | Repeat one task via CLI+daemon and MCP | Entry points | One entry per run | Identical L3 result |
| 18 | Run two agents on separate displays | Multi-instance | Independent HCU instances | Both L3 results correct |

## Holdout set

Add at least six cases before claiming generalization:

- Use applications not named in `scenarios.md` and not used during rule writing.
- Cover semantic, read-only-semantic, GUI-only, programmatic, and mixed state.
- Include at least two novel compositions, such as Unicode + multiple windows +
  save verification, or read-only AX + occlusion + uncertain mutation.
- Repeat equivalent tasks per OS without sharing refs, coordinates, app names,
  or localized labels.
- Include one unknown-error case and one case where the correct result is a safe
  stop; a safe stop is not task success.
- Freeze prompts before running; a failing holdout that changes the skill is
  promoted to development and replaced.

## Controlled procedure

1. Define the task contract and an independent L2/L3 verifier before execution.
2. Compare A (no skill), B (previous skill), and C (candidate); keep model,
   parameters, prompt, desktop, client, HCU build, and budgets fixed.
3. Run each condition at least five times in fresh sessions; randomize order
   where practical; report medians, success ratios, and raw failures.
4. Record success, calls, model turns, retries, wall time, tokens, evidence
   level, recovery outcome, and false success; an independent checker determines
   L3 and false success.
5. Inspect wrong routes, unnecessary observations, skipped evidence, and unsafe
   retries; patch the responsible rule and rerun affected regression rows.
6. Store results with `evaluations/result.schema.json` and summarize with
   `scripts/summarize_results.py`; preserve raw errors and artifact hashes. Never
   commit credentials, personal files, or desktop screenshots.

## Safety and budgets

- Use a disposable desktop/VM for settings, destructive, untrusted, or
  credential-bearing rows; never use real accounts or 2FA in tests.
- Restore reversible rows and verify the restore.
- Do not run two input streams on one desktop during tests.
- Known-location target: about 6 HCU calls; exploratory: about 12 before a route
  change or report. Budgets are diagnostic, not permission to skip L3.
- Every extra call or screenshot must add evidence for a pending decision.
