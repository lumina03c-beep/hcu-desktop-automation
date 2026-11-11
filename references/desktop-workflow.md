# Desktop workflow

Desktop stages use Microsoft HCU; the existing HCU skill and its references
remain the authority for AX/GUI behavior, refs, batching, waits, and platform
rules.

## Readiness and selection

- Confirm HCU is installed, the session can reach `AX` and `GUI`, and the
  desktop is usable before mutation. A successful build or handshake is not
  readiness.
- Prefer AX for named controls, roles, values, states, menus, dialogs, and text;
  use GUI for canvases, images, dragging, occluded targets, and controls AX
  cannot address.
- Do not alternate screenshots and AX reads of an unchanged state.
- Desktop-only tasks do not require Browser readiness.

## Refs and session state

- Use only refs from the current HCU session; refs are neither selectors nor
  persistent identifiers.
- After navigation, window replacement, or a top-level window change, re-read
  `apps` or `find` before acting.
- Never store refs, GUI frames, or old coordinates in the Workspace.

## Batching and editing windows

- Batch deterministic steps in one window when target, state, and risk are
  known; split at window changes, evidence-dependent decisions, uncertain
  state, and `R2` boundaries. Obey HCU action limits.
- In windows whose title changes with content, prefer one action per call plus
  `settle`; a multi-step batch can abort with `effect_unknown` when window
  identity changes mid-batch.
- After `effect_unknown`, read the delivered state and send only the remaining
  steps as single actions; never resend text that may have landed.

## Bulk text

- Deliver multi-line content through the clipboard and send one paste keypress;
  never type a keystroke storm.
- Select the whole document once when replacing; verify through app readback or
  a saved file (AX values can collapse markdown markers).
- Restore the clipboard when task or environment policy requires it.

## File-first creation

- When the oracle is the saved file, create it through auxiliary tools and open
  it with the application's launch argument instead of driving an in-app
  New-file dialog; this avoids title-change batch traps.
- Drive in-app creation only when the process itself is contracted.

## Environment preflight

- Resolve the real Desktop known folder and launchable app paths before the
  first input; prefer the OS known-folder API over a hard-coded path.
- Cache only validated semantic facts in `workspace.environment`; a missing or
  changed path is a cache miss, not a task failure.

## Verification and recovery

- Read effect, diff, windows, `input_emitted`, and `completed`; an accepted
  action is not a business result. Verify saved files by parsing them on disk
  and use `L3` for persisted outcomes.
- Honor HCU error semantics (`stale_ref`, `gui_frame_stale`, `window_changed`,
  `wait_timeout`, `effect_unknown`, `partial_input_possible`): never replay
  input that may have landed; re-observe and retry only with new evidence.
- Keep the two-strike rule and safe-stop discipline.

## Desktop-to-Browser handoff

1. Record the last verified state and artifact paths.
2. Record the next Browser action.
3. Return control to the Main Agent; never write the Workspace directly.
