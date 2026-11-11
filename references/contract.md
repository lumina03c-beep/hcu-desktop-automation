# HCU contract essentials

This file is the **HCU-specific execution contract**. The shared,
engine-neutral task contract is in `references/task-contract.md`, and the
authoritative task state is defined by `references/workspace-policy.md` and
`schemas/workspace.schema.json`. Do not apply HCU-specific limits, refs, or
batching rules to ego-browser, and do not weaken them to unify architecture.

## Identity and refs

- `aN` application -> `wN` top-level window -> `rN` element.
- A ref is a short-lived capability, not a selector. It stays bound to one
  window and fails as stale when its exact target disappears or is replaced.
  Never build refs; copy them from results.
- Refs are session-scoped: valid across calls of one entry point, not across
  `call` processes, and expired after a daemon restart (counters persist, old
  numbers are not reissued). There is no fixed TTL: a ref lasts while its
  session lives and its exact target remains.
- `apps` may report `inventory_complete=false` with `inventory_issues`.
  Confirmed windows stay usable; missing windows remain unknown. Title-based
  selection, implicit focus, and window waits require a complete listing.
  A missing window does not prove that a close succeeded.

## Observation

Before acting, confirm that the observation is sufficient for the pending
decision: target identity, state owner, current value, preconditions, focus or
actionability, live ref/frame, and a way to verify the result. An incomplete
inventory or tree means unknown, not absent. Do not treat a visually hidden,
AX-unreadable, truncated, or non-addressable target as equivalent.

- Modes: `apps`, `observe`, `find`, `act`. CLI/SDK also expose `read`
  (`{"mode":"read","refs":[...]}`): live resolve per ref, no tree walk. The MCP
  server rejects `read`.
- `observe` returns a compact working tree or a diff. The canonical tree stays
  complete; the projection drops empty leaves and collapses neutral containers,
  while `find` and actions query canonical records. An explicit root stays
  visible even without a label.
- `scope`: `content` for one identifiable page/document root, `window` for
  chrome, menus, dialogs, settings. The result states why a scope expanded.
- `find` query: `role`, `name_equals`, `name_contains`, `text_equals`,
  `text_contains`, `state`. Results may be paginated (`next_cursor`). A
  zero-result find lists at most five nearby candidates; suggestions do not
  change the query or send input. A zero result can be a formatting artifact
  (for example `1,161` vs `1161`): read the field or match a stable substring
  before concluding absence.
- Budgeted output: long sibling runs lose elements from the end first; one
  `/omitted: "budget nodes=N ..."` line counts the rest. Cell values are shown
  after the name, at most 40 code points plus an ellipsis.
- Incomplete reads: `coverage:"partial"` carries `acquisition` with
  `reported_missing_nodes` and `reasons`; `recover.structural_budget` describes
  output pruning, `recover.acquisition` unfinished reads. An unread branch can
  contain more nodes than the provider could count.
- A window tree read is capped at about 15 s; a larger tree returns partial
  coverage. Unread controls are not addressable; use `find`, a subtree root,
  or GUI.
- `observe` evidence: default `diff`; explicit `tree`, `full` (tree plus
  screenshot), `screenshot`, or `none`. `none` only when readback is
  unnecessary; the report then says unknown. `full`/`screenshot` also register
  the GUI frame.

## Risk and evidence contract

Classify before batching:

- `R0`: read-only inspection. Narrow the read to the pending decision.
- `R1`: reversible local mutation. Batch only deterministic steps with a known
  target and readback; restore temporary state when the task requires it.
- `R2`: high-impact, hard-to-reverse, privacy-sensitive, or externally visible
  mutation. Isolate it, preview the exact target and payload, obtain required
  confirmation, and verify the final outcome. Never hide R2 inside an R1 batch.

Declare the minimum sufficient evidence before acting:

- `L1 action`: input was delivered or the tool accepted a call.
- `L2 state`: the application, control, dialog, or visible state changed.
- `L3 outcome`: the requested business result, external receipt, or persisted
  artifact is independently verified.

Use L3 for saved files, external submission, deletion, purchase, publishing,
security changes, and other R2 outcomes. If only L1 is available, continue
observing; if L3 is unavailable, report the uncertainty rather than success.

## Actions (`act`)

- Up to 64 ordered steps; one `act` works in one window. The whole batch is
  validated before input; argument errors reject it. The first failing step
  stops the batch and reports `completed`/`requested`.
- Step types: `click`, `type`, `keypress`, `set_value`, `select`, `scroll`,
  `activate`, `close`, `wait`.
- `click` is semantic and may activate an item, not merely select it.
  `activate`/`close` take a `wN` or a window-title substring; `close` goes last
  in a batch.
- `type` sends real text. Document `set_value` selects the full range before
  replacing it; clearing a document sends Delete. Semantic Value/RangeValue
  writes on plain edits are different from document replacement.
- `select`: whole element, one unique substring, or a range through `to_ref`
  (text or table cells). It reads the selection back and reports it; a
  mismatch or unreadable result fails with `effect_unknown`. Cross-element
  ranges and duplicate/missing text fail before input.
- `scroll`: AX takes direction/pages; GUI takes `scroll_x`/`scroll_y` at a
  point.
- Waits: `window` (title on the whole desktop), `query` (element in any visible
  window of the batch application, dialogs/popups included), `ref` with
  `value`/`state`/`text`, `text` alone, `settle:true`, and `gone:true`.
  Timeouts sum to at most 60 s (the batch is validated before input); an
  omitted `timeout_ms` is 5000. A wait sends no input. A timeout fails the step
  and stops the batch. After a `window` wait, ref-less keys/text go to that
  window; after a `settle`, they go to the window that holds focus. After a
  `query` wait, ref-less keys/text go to the focused window; after a `text` or
  `gone` wait, the same focused-window rule applies. An act of only waits
  sends no input. A title wait needs a substring you expect to appear; when the
  title pattern is uncertain, wait on a `query`/`ref`/`text` or read the diff
  instead.
- `settle` holds when the UI changed after the input step and then stayed
  unchanged for 0.4 s. It names what changed and fails with "no change" only
  when nothing changed. A UI that keeps changing passes at the timeout with a
  note. It measures stillness, not semantic readiness; content arriving later
  needs a `text`/`query` wait or a fresh read.
- Split at the next decision that needs new evidence, at a window change, or
  before actions that depend on a late state. Do not add a wait the evidence
  line already answers; `effect`/`windows` may prove the result.

## Results

- Status line: `ok`, on failure `code`, `path`, `message`, `hint`; then
  `input_emitted`, `completed`, `requested`. Recovery fields include
  `continuation`, `retry_same_request`, `partial_input_possible`,
  `observation_required`, and an inner `failure_code`.
- One `effect` line per targeted element: changed fields, `no visible change`,
  `unknown (reason)`, or `gone`. `(only state flags changed in this window)`
  means no page, content, or window changed; if the control should have
  switched something, the application did not respond.
- A `windows` line names windows that opened, closed, or took focus, with
  usable `wN` refs.
- Removed diff lines omit refs; `absent_refs` lists removed refs (ranges such
  as `r40..r43` are inclusive) and they must not be reused.
- A successful wait proves its condition. A final observation can fail
  separately (`observation_failure_code`, `observation_required`) after input
  was sent.

## GUI

- GUI is full-desktop and not tied to an application. The image is scaled to
  fit within 1366x768; coordinates are pixels of the returned image and are
  mapped back per axis.
- A screenshot establishes a layout lease. Before each coordinate action the
  window under that point is checked; if it changed, the action fails before
  input with `gui_frame_stale` and a fresh screenshot is returned.
- A screenshot action must stand alone. `zoom` must stand alone, sends no
  input, and its evidence line carries `{frame, region, width, height,
  scale_x, scale_y}`. Convert with `x = region[0] + u/scale_x`,
  `y = region[1] + v/scale_y`; never pass zoom pixels directly. The SDK helper
  `zoom_point` performs the same conversion.
- Actions: `click`, `double_click`, `move`, `drag` (path), `scroll`, `type`,
  `keypress`, `wait` (one second, at most 20 s per batch). `settle_ms`
  (default 800, max 3000) measures final visual stillness, not success; it is
  not the AX `settle` step.
- End a GUI batch after an action that opens, closes, moves, resizes, switches,
  or navigates a window/dialog; plan the next coordinates from the final
  screenshot.

## Budgets

- 64 actions is a limit, not a goal. Every extra round trip and screenshot is a
  real cost (official measurements: about 7 s per model turn and about 2.4K
  tokens per 1080p screenshot).
- Prefer `find` over a full `observe`, diff/effect over a new tree, and one
  screenshot only when pixels are the required evidence.
- Large outputs may be written to files (`COMPUTER_USE_OUTPUT_*`); inline text
  is capped (`COMPUTER_USE_MAX_INLINE_CHARS`). The server sends real input to
  the signed-in desktop; treat it accordingly.
