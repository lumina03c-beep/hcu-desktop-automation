# Generalization and regression testing

Measure completed, independently verified outcomes rather than tool calls that
merely returned `ok`. Keep application recipes in the development set and prove
generalization on applications and task combinations never used to write rules.

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

## Holdout generalization set

Create at least six additional cases before claiming generalization:

- Use applications not named in `scenarios.md` and not used during rule writing.
- Include semantic, read-only-semantic, GUI-only, programmatic, and mixed state.
- Include at least two novel compositions, such as Unicode + multiple windows +
  save verification, or read-only AX + occlusion + uncertain mutation.
- Repeat equivalent semantic tasks on each available OS without sharing refs,
  coordinates, application names, or expected localized labels across runs.
- Include one unknown-error case and one case where the correct result is a safe
  stop. A safe stop is not counted as task success.
- Freeze holdout prompts before running. If a holdout failure changes the skill,
  promote that case to development and replace it with a new holdout case.

## Controlled procedure

1. Define the task contract and an independent L2/L3 verifier before execution.
2. Compare A: no skill, B: the previous/basic skill, and C: the candidate skill.
   Keep model, parameters, prompt, initial desktop, client, HCU build, and step,
   time, and token budgets fixed.
3. Run each condition at least five times in fresh sessions. Randomize run order
   where practical; report medians, success ratios, and raw failures rather than
   selecting the best run.
4. Record task success, HCU calls, model turns, retries, wall time, token usage,
   evidence level, recovery outcome, and false success. An independent checker
   determines L3 and false success, not the agent's own completion claim.
5. Inspect wrong routes, unnecessary observations, skipped evidence, and unsafe
   retries. Patch only the responsible rule and rerun affected regression rows.
6. Store results using `evaluations/result.schema.json`; summarize them with
   `scripts/summarize_results.py`. Preserve raw errors and artifact hashes when
   available. Do not commit credentials, personal files, or desktop screenshots.

## Core metrics

| Metric | Definition |
| --- | --- |
| Task Success Rate | Independently verified task completions / runs |
| False Success Rate | Agent claims success but independent verification fails / runs |
| Interaction Count | HCU calls, reported separately from shell/API calls |
| Model Turn Count | Model decision rounds per run |
| Completion Latency | Wall time from task start to verified terminal state |
| Token Consumption | Input/output tokens when available; otherwise explicitly unknown |
| Recovery Rate | `recovered` / eligible failed steps; safe stops reported separately |

## Safety and budgets

- Use a disposable desktop/VM for settings, destructive, untrusted, or
  credential-bearing rows; never use real accounts or 2FA in tests.
- Reversible rows must be restored and independently checked after restore.
- Do not run two input streams on one desktop during tests.
- Known-location target: about 6 HCU calls; exploratory target: about 12 before
  a route change or report. Budgets are diagnostic, not permission to skip L3.
- Every extra call or screenshot must add evidence for a pending decision.
