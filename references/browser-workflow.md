# Browser workflow

Browser stages use the installed ego-browser skill; its current guide is the
only authority for API names, options, and limits. This file defines only the
Dynamic UI RPA contract around it.

## Readiness

Before the first Browser action, run the ego-browser entry command, read the
full guide, and confirm its end marker. If the guide is missing, truncated, or
fails, Browser is not ready: do not substitute another driver, guess APIs, or
treat a printed guide as a live session.

## TaskSpace discipline

- Use exactly one ego TaskSpace per user goal; create it once and resume it by
  `spaceId`.
- Do not open a second TaskSpace to recover, and do not finish it during a
  temporary Desktop handoff; call `finish()` only when the whole task is
  complete or explicitly aborted.
- The TaskSpace is the live browser session, not the Task Workspace.

## Observation and batching

- Take one orientation snapshot at stage entry when the layout is unknown; then
  extract only decision fields with `evaluate`, `find`, or `waitForFunction`.
- Use screenshots and coordinates only when useful DOM semantics are absent.
- Default stage shape: navigate → actions → wait for a terminal condition
  (`waitForURL`, `waitForSelector`, `waitForFunction`) → targeted verification,
  printing only the terminal evidence.
- Split at navigation, dynamic branches, uncertain results, high-risk actions,
  and evidence-dependent decisions; use documented waits, not fixed delays.
- Keep extraction inside the browser script and return only its result.
- Express deterministic selection or branching as in-page `evaluate` logic in
  the same script, and end it with a structured terminal receipt (title, URL,
  state) that doubles as `L2` evidence.

## Page lifecycle and cost

- Reuse the existing Page and navigate it; do not open a Page per step.
- Confirm control is still yours before creating a Page; a command refused for
  user control costs a round trip and proves nothing.
- Register long-lived products (playing media, an open result view) as planned
  artifacts at stage start, keep them during cleanup, and pass an explicit keep
  list to `finish()`.
- After a user takeover, re-observe once and continue from the last verified
  state; do not rebuild completed stages.

## Files

- Prefer Browser upload when the current guide supports the required file
  input; switch to Desktop only when a native dialog is genuinely required.
- For downloads, follow the guide's event wait and save to an absolute path;
  verify the file exists, parses, and satisfies the task before completing.

## Verification and stops

- A receipt proves only dispatch; a click or accepted request is not business
  success. Verify through page state, business object state, file content, or
  an external receipt, using `L3` for persisted or externally visible results.
- If the user takes control or the TaskSpace becomes inactive or unassigned,
  stop immediately, save the last verified state, and report the blocker; do
  not retry or route around it.
