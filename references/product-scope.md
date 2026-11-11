# Product scope

Dynamic UI RPA is a staged execution discipline for tasks whose required truth
lives in live browser UI or native desktop UI. It is not a general automation
platform and not a replacement for workflow engines.

## In scope

- Browser tasks executed through the installed ego-browser skill.
- Desktop tasks executed through Microsoft HCU.
- Hybrid tasks that must cross Browser and Desktop inside one user goal.
- A single authoritative Task Workspace per user task.
- Stage-level routing, verified outcomes, cross-engine handoff, and recovery.
- Auxiliary shell/file/CLI support used inside a UI task.

## Out of scope

- Pure API, CLI, batch, scheduled, or headless workflow automation.
- A third UI engine, a new browser engine, or a new desktop engine.
- A standalone RPA client, Windows floating UI, or workspace web app.
- A workspace daemon, database, WebSocket service, or independent runtime.
- Automatic management of user passwords, 2FA, or long-lived credentials.
- Modifying ego-browser or HCU upstream implementations.

## Engine boundaries

- Browser owns web page state: DOM, tabs, signed-in sessions, browser
  uploads/downloads, and browser-visible business results.
- Desktop owns native window state: Office apps, system dialogs, settings,
  native canvases, and OS-level visual state.
- Programmatic tools own files and services only when no live UI session owns
  the required truth.
- A Browser upload stays in Browser unless a native Windows dialog is truly
  required.
- A Desktop task never requires Browser readiness, and a Browser task never
  requires Desktop readiness.

## Required truth

A task belongs to this skill only when the requested outcome depends on live
UI state or must be verified through a UI-owned surface. If the same outcome
is more reliably achieved with a documented API, CLI, or file operation, use
that route directly and do not enter a UI loop.

## Non-goals preserved by design

- Do not copy ego-browser or HCU manuals into this repository.
- Do not turn auxiliary tools into a first-class routing engine.
- Do not claim a UI capability before the relevant engine is actually ready.
- Do not turn a safe stop or an unresolved unknown into a completed task.
