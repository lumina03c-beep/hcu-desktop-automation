# Errors, recovery, and entry-point lifecycle

## Principles

1. Read the Workspace before acting; it is the authoritative state record.
2. Classify failure by whether input may have landed, not by engine name.
3. Never replay `effect_unknown`, `partial_input_possible`, or any unverified
   mutation without a fresh observation.
4. Keep HCU error semantics; do not translate them across engines.
5. A handoff failure preserves the Workspace and the last verified state; it
   never restarts the task or repeats a completed side effect.
6. Keep `recovered`, `task_completed`, `safe_stopped`, and `failed` distinct.
7. The two-strike rule spans engines; switching resets nothing.

## Read fields first

A failed result carries `code`, `path`, `message`, `hint`, then `input_emitted`,
`completed`, `requested`. Recovery fields include `continuation`,
`retry_same_request`, `partial_input_possible`, `observation_required`, and an
inner `failure_code`. These, not the top-level code alone, define the next step.
Never infer "nothing happened" from a failure.

## Mutation ledger

For every state-changing sequence track: last confirmed state, requested
mutation, exact target and payload, whether input may have landed, observed
effect, current unknown, next safe read, restoration requirement. Use it to
prevent duplicate external actions and to distinguish recovery from a safe stop.

## Behavior classes

- **No input sent**: `invalid_argument`, `stale_ref`, `gui_frame_stale`,
  `window_not_found`, `ambiguous_window`, `no_focused_window`,
  `app_unavailable`, `permission_denied`.
- **Input may have landed**: `wait_timeout`, `window_changed`, `effect_unknown`,
  `runtime_error`.
- **Tool stopped on its own**: the returned stop response overrides all other
  fields; honor it.

## Public codes

| Code | Meaning | Next step |
| --- | --- | --- |
| `invalid_argument` | Schema, query, or batch validation failed | Fix the request; nothing was sent |
| `stale_ref` | Ref target disappeared or was replaced | Re-find/observe, then act with the new ref |
| `gui_frame_stale` | Window under the point changed; nothing sent | Plan from the returned screenshot |
| `window_not_found` | Named window not in complete inventory, or surface changed | Read `apps`; re-derive the window |
| `ambiguous_window` | Title matched several windows | Use a `wN` or narrow the title |
| `no_focused_window` | Ref-less keys/text reached no known window | Activate a window or use a ref |
| `app_unavailable` | Application intent cannot be resolved | Try a concrete window, or launch the app if allowed |
| `permission_denied` | OS or call scope denied the action | Fix permissions in the OS, restart the provider; do not retry |
| `wait_timeout` | Wait condition not observed | Inspect with a fresh read before acting |
| `window_changed` | Target window closed/changed during the call | Read `apps`; continue only from new evidence |
| `effect_unknown` | Input may or may not have taken effect | Observe/readback before another mutation |
| `runtime_error` | Provider raised an internal error or timed out | Read `message`/`hint`; retry a read once unless forbidden |
| `stop` | Run stopped deliberately | Report the stopping reason; do not replan silently |

Inner `failure_code` values refine `runtime_error` and `effect_unknown`:
`point_owner_mismatch` (an AX click is covered or the pointer belongs to another
window; read `input_emitted`), `coordinate_target_unverified` (the screenshot
does not prove an eligible covering window), `window_blocked` (a modal dialog
blocks the window behind it on Linux). Treat unknown inner codes generically:
read `message`/`hint`, inspect state, change channel.

## Recovery rules

- Reads: one retry on a transient `runtime_error` unless forbidden.
- Mutations: retry only with new evidence; `retry_same_request:true` means the
  same request is still safe, not "blindly replay". Never replay input that may
  have landed.
- After two attempts on the same hypothesis without new evidence, change
  mechanism or channel, or stop and report. Do not nudge coordinates, add stray
  Enter, stack waits, or relaunch to escape ambiguity.
- `user_control` is a normal ownership transfer: stop, persist, report, resume
  only when the user asks.
- A batch stopped after step 1 with `effect_unknown` due to a window identity
  change proves only that step 1 was attempted: read the delivered state, then
  continue single-step or switch to an auxiliary content channel.
- A zero-result `find` or wait can list nearby candidates; compare before
  acting; they do not match the query.
- Missing from an incomplete inventory proves nothing about closes.
- After navigation or any top-level window open/close, re-read `apps`/`find`.
- `runtime_timeout` arrives as `runtime_error` with `mutation_unknown` and often
  `partial_input_possible`: inspect fresh state once; never replay.

## Recovery outcome

`recovered` = a failed step resumed safely; `task_completed` = the success
oracle passed; `safe_stopped` = further mutation avoided but the goal remains
unfinished; `failed` = neither recovery nor a safe final state was proved.
Protocol adherence or a safe stop alone is not recovery success.

## Entry points and state

| Entry | Refs valid | Notes |
| --- | --- | --- |
| MCP server (in-process) | Session of that server | Refuses input while a daemon serves the desktop; reads still answered |
| CLI + daemon | Across CLI commands | One daemon per desktop; input lock serializes; wait-only acts allowed while running |
| Python SDK | Across calls | Same daemon; `act` defaults to `observe:"none"`; request a diff when needed |
| `mcp --attach SOCKET` | Shared with daemon | Use when MCP and CLI/SDK coexist; never run two input streams |

- One input stream per task; `--attach` joins the daemon's stream, not a second.
- `request_id`: one run per id; replay returns the first result for 10 minutes;
  a restart clears the cache. Ref counters persist across daemon restart; old
  refs expire.
- A `call` process does not preserve refs; do not mix it with a daemon session.
- The input lock admits one call at a time, including waits; plan around it.

## CLI exit codes

`0` success, `2` invalid_argument, `3` wait_timeout, `4` stale_ref or
gui_frame_stale, `5` window_changed or effect_unknown, `6` window/app not found,
`10` runtime_error, `64` bad command line.
