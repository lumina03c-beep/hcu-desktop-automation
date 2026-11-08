# Channel routing

Pick the channel by **where the state lives**, not by which tool is convenient.

## State ownership

| State to change | Route | Reason |
| --- | --- | --- |
| Data, code, config, archives, media that no app holds open | shell + format-aware library/CLI; inspect the real format first | Exact, scriptable, verifiable by parsing |
| A document an app has open | that app: AX for menus/dialogs/fields, GUI for what AX lacks | Its in-memory copy is what gets saved |
| Application or system settings | settings UI through AX; config file/CLI only when the app is closed or rereads it | A running app can write cached settings back |
| Web pages, forms, signed-in sites | the open browser session (endpoint if exposed, else AX/GUI) | Login, cookies, and tabs exist only there |
| Canvases, images, drawings, layout | the editor: AX for menus/dialogs, GUI for pixels and dragging | Visual objects have no names to address |
| Messages, mail, calendar, accounts | authorized API/CLI for outcome-only work, otherwise the owning client via AX/GUI | Choose by session ownership and required evidence, not by app habit |

## Route record

Before the first mutation, record internally:

- `state_owner`: which file, service, session, or open app owns the truth;
- `primary_channel` and `fallback_channel`;
- `evidence_channel`: the cheapest independent proof of the requested outcome;
- `switch_condition`: the observation or error that invalidates the current route.

Re-route when ownership, addressability, visual necessity, or evidence needs
change. Do not keep using a channel merely because earlier steps used it.

## Programmatic first

- Files not held open: use shell, a format-aware library, or a CLI. Check the
  real format and metadata before choosing a parser; verify by parsing the
  saved artifact.
- An open document belongs to its application; a saved file that is still open
  remains owned until it is closed. If the app cannot reach a needed property,
  save and close it (or confirm no unsaved changes), edit the file, parse it,
  and reopen only if the task requires the open view.
- Settings: prefer the UI while the app runs; edit config only when it is
  closed or known to reread on change.
- A documented, authorized automation endpoint that already exposes the target
  state acts inside that session or service. This applies to browsers, mail,
  calendars, messaging, Office, and other apps, not only to local files. Probe
  once, early. After one failed probe, use AX or GUI. Do not rebuild a site or
  client workflow with blind shell HTTP requests, and do not start another
  browser, profile, or client merely to avoid the current UI.
- Prefer endpoints with typed resources, authorization, idempotency, and
  receipts for high-impact outcomes. Preserve the user's explicit UI method or
  visible-state requirement even when an API is available.
- Discover commands from the app's menus, dialogs, help, or one narrow manual
  query. Do not dump whole help texts or scan binaries.

## Explicit method vs outcome

- An outcome-only request may be met by any general route.
- Honor an explicitly exclusive method, a method that is itself the user's
  purpose, and requirements about visible state. Naming an app does not by
  itself exclude an equivalent route; "leave the page open" requires the open
  page.

## AX vs GUI inside one app

- AX: named controls, roles, values, states, menus, dialogs, keyboard. Find by
  role/name; use content scope for one page/document root and window scope for
  chrome, menus, dialogs, settings.
- GUI: canvases, images, layout, dragging, scrolling, controls AX cannot read,
  and occluded/offscreen targets. A screenshot must stand alone; `zoom` only
  looks and its pixels never go directly into GUI `x`/`y`.
- AX `observe:"full"` or `"screenshot"` returns the same full-desktop frame
  and registers it as the current GUI frame; plan coordinates from it without
  another screenshot.
- Do not alternate screenshots and AX reads of an unchanged state. Pick the
  channel that can supply the evidence the task requires.
- Channel bias varies by model and task; decide from live state, not habit.

## Evidence by channel

- AX proves tree-visible state only. GUI proves returned pixels and input
  delivery only. Neither proves file contents, persistence, or network state;
  verify those through the shell or the application.
