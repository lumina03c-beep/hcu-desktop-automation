# Dynamic UI routing

Routing has two levels:

1. **First level**: choose Browser, Desktop, or Hybrid for a task stage.
2. **Second level**: inside Desktop, choose AX, GUI, or a programmatic support
   route using the existing HCU state-ownership rules.

Route by where the required truth lives, not by tool habit or application name.

## First-level routing

| Required truth or interaction | Route |
| --- | --- |
| Web page, SPA, browser form, signed-in site state | Browser |
| Browser upload/download and browser-visible result | Browser |
| Web canvas with DOM semantics unavailable | Browser, visual mode |
| Native window, Office app, settings UI, system dialog | Desktop |
| Native canvas, drawing, video editing, pixel-only desktop UI | Desktop |
| Task needs both Browser and Desktop stages | Hybrid |
| Pure file, API, CLI, or data task with no UI truth | Programmatic; not this skill's first-level route |

## Browser-first

- For web work, Browser is the default.
- A browser file upload stays in Browser when the current ego-browser guide
  supports the required input flow.
- Do not switch to Desktop merely because uploads often open a native dialog.
- Switch only when a native dialog is genuinely required and Browser cannot
  complete the stage.

## Desktop

- Use Desktop for native windows, Office applications, system settings,
  native file dialogs, canvases, and visual desktop state.
- Desktop-only tasks do not require Browser readiness.
- Use HCU's AX/GUI rules for the internal channel choice.

## Hybrid

- Use Hybrid only when the user goal requires stages in both engines.
- Hybrid is not a per-click toggle.
- One task uses one Workspace and may contain multiple handoffs.
- Temporary engine switching does not end the task or create a new task.

## Readiness

Judge readiness independently:

- **Browser Readiness**: the current ego-browser guide loads and a real
  browser session is usable.
- **Desktop Readiness**: HCU is installed and the current client can reach
  `AX` and `GUI`.
- **Task Readiness**: the engines required by the planned stages are ready.

A Browser-only task must not fail because HCU is missing. A Desktop-only task
must not fail because ego-browser is missing. A Hybrid task requires only the
engines its stages actually use.

Do not treat a guide print, build success, config write, or handshake as
readiness.

## Stage-level routing

- Route at task-stage level.
- Do not re-run full routing after each click.
- Re-evaluate only when the target UI environment, state ownership,
  addressability, or required interaction materially changes.
- If a single action fails, first recover inside the current engine; do not
  switch engines as a reflex.

Before a first mutation, record:

- `state_owner`
- `primary_engine`
- `fallback_engine`
- `evidence_channel`
- `switch_condition`

## Switch guardrails

Consider switching only when:

1. The operation target moves to another UI environment.
2. The current engine cannot perform a required interaction.
3. The current engine cannot observe the required state.
4. Recovery inside the current engine is impossible.
5. The user explicitly requests a different engine.

Before switching, check:

- Was the target misidentified?
- Did the page or window change?
- Are refs stale?
- Is a wait missing?
- Is there a permission problem?
- Does the task truly need the other engine?

If the answer is no, recover locally.

## HCU internal routing

| State to change | HCU channel |
| --- | --- |
| Data, code, config, archives, media no app holds open | shell + format-aware library; verify by parsing |
| A document an app has open | owning app: AX for semantics, GUI for pixels |
| Application or system settings | settings UI via AX; config only when safely reloadable |
| Web pages through HCU | AX/GUI only when Desktop owns the browser window |
| Canvas, images, drawings, layout | GUI for pixels; AX for menus/dialogs |
| Messages, mail, calendar, accounts | owning client via AX/GUI, or authorized API when outcome-only |

## Programmatic support

- Programmatic tools are auxiliary.
- They may parse files, validate artifacts, or prepare data inside a UI task.
- A stage whose oracle is outcome-only may deliver through auxiliary tools
  (data API, direct file write); the UI engine joins only for process
  requirements or live-UI oracles.
- They never become a third first-level UI engine.
- They do not trigger Browser/Desktop re-routing by themselves.

## Route record

Store the route decision in the Workspace stage or route record:

- Primary engine and fallback.
- Reason for any switch.
- Evidence channel for the stage.
- Switch condition that would invalidate the plan.

Re-route when ownership, addressability, visual necessity, or evidence needs
change. Do not keep an engine merely because earlier steps used it.
