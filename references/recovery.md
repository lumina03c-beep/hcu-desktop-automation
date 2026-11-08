# Errors, recovery, and entry-point lifecycle

## Read fields first

A failed result carries `code`, `path`, `message`, `hint`; then `input_emitted`,
`completed`, `requested`. Recovery fields include `continuation`,
`retry_same_request`, `partial_input_possible`, `observation_required`, and an
inner `failure_code`. These, not the top-level code alone, define what to do.
Never infer "nothing happened" from a failure.

## Mutation ledger

For every state-changing sequence, track the last confirmed state, requested
mutation, exact target and payload, whether input may have landed, observed
effect, current unknown, next safe read, and restoration requirement. Use this
ledger to prevent duplicate external actions and to distinguish task recovery
from a safe stop.

## Behavior classes

- **No input sent**: `invalid_argument`, `stale_ref`, `gui_frame_stale`,
  `window_not_found`, `ambiguous_window`, `no_focused_window`,
  `app_unavailable`, `permission_denied`.
- **Input may have landed**: `wait_timeout`, `window_changed`,
  `effect_unknown`, `runtime_error`.
- **Tool stopped on its own**: a returned stop response overrides all other
  fields. Honor it.

## Public codes

| Code | Meaning | Next step |
| --- | --- | --- |
| `invalid_argument` | Schema, query, or batch validation failed | Fix the request; nothing was sent |
| `stale_ref` | Ref target disappeared or was replaced | Re-find/observe, then act with the new ref |
| `gui_frame_stale` | Window under the point changed; nothing sent | Plan from the returned screenshot |
| `window_not_found` | Named window not in complete inventory, or surface changed | Read `apps`; re-derive the window |
| `ambiguous_window` | Title matched several windows | Use a `wN` or narrow the title |
| `no_focused_window` | Ref-less keys/text reached no known window | Activate a window or use a ref |
| `app_unavailable` | Application intent cannot be resolved | Try a concrete window, or launch the app if the task allows |
| `permission_denied` | OS or call scope denied the action | Restore the permission in the OS, then restart the provider; do not retry the same request |
| `wait_timeout` | Wait condition not observed | Inspect with a fresh read before acting |
| `window_changed` | Target window closed/changed during the call | Read `apps`; continue only from new evidence |
| `effect_unknown` | Input may or may not have taken effect | Observe/readback before another mutating attempt |
| `runtime_error` | Provider raised an internal error or timed out | Read `message`/`hint`; retry a read once unless forbidden |
| `stop` | Run stopped deliberately | Report the stopping reason; do not replan silently |

Inner `failure_code` values refine `runtime_error` and `effect_unknown`:
`point_owner_mismatch` (observed when an AX click is covered or the pointer
belongs to another window; in observed runs the click was refused before
dispatch, but always read `input_emitted`), `coordinate_target_unverified` (the
screenshot does not prove an eligible covering window), `window_blocked` (a
modal dialog blocks the window behind it on Linux). Treat unknown inner codes
generically: read `message`/`hint`, inspect state, change channel.

## Recovery rules

- Reads: one retry on a transient `runtime_error` unless the result forbids it.
- Mutations: retry only with new evidence (`retry_same_request:true` does not
  mean "blindly replay"; it means the same request is still safe to send).
  Never replay input that may have landed.
- After two attempts on the same hypothesis without new evidence, change
  mechanism or channel, or stop and report. Do not nudge coordinates, add a
  stray Enter, stack waits, or relaunch to escape ambiguity.
- A zero-result `find`/wait can list nearby candidates; compare them before
  acting; they are not a result for the query.
- Missing window from an incomplete inventory proves nothing about closes.
- After navigation, window replacement, or any top-level window open/close,
  refs can change or renumber: re-read `apps`/`find` before acting.
- `runtime_timeout` arrives as `runtime_error` with `mutation_unknown` and often
  `partial_input_possible`. Inspect fresh GUI/AX state once; do not replay the
  same text or click.

## Recovery outcome

Record recovery separately from task completion: `recovered` means a failed
step resumed safely; `task_completed` means the original success oracle passed;
`safe_stopped` means further mutation was avoided but the goal remains
unfinished; `failed` means neither recovery nor a safe final state was proved.
Never count protocol adherence or a safe stop alone as recovery success.

## Entry points and state lifecycle

| Entry | Refs valid | Notes |
| --- | --- | --- |
| MCP server (in-process) | Session of that server | Refuses input while a daemon serves the desktop; reads still answered |
| CLI + daemon | Across CLI commands | One daemon per desktop; input lock serializes; wait-only acts allowed while running |
| Python SDK | Across calls | Same daemon; `act` defaults to `observe:"none"`, request a diff when needed |
| `mcp --attach SOCKET` | Shared with daemon | Use when MCP and CLI/SDK must coexist; never run two input streams |

- Use one input stream per task. `--attach` joins the daemon's stream; it does
  not add a second one.
- `request_id`: one run per id in a running daemon; replay returns the first
  result for 10 minutes. A restart clears the cache.
- Ref counters persist across daemon restart; old refs expire.
- A `call` process does not preserve refs between calls; do not mix it with a
  daemon session.
- Input lock: one call at a time, including waits; plan around it rather than
  racing other sessions.

## CLI exit codes

`0` success, `2` invalid_argument, `3` wait_timeout, `4` stale_ref or
gui_frame_stale, `5` window_changed or effect_unknown, `6` window/app not
found, `10` runtime_error, `64` bad command line.
