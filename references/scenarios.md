# Scenario playbooks

Use these as fallback examples after deriving the task contract, not as fixed
recipes or proof of generalization. Re-resolve state ownership, preconditions,
refs, risk, and success evidence on every run. Prefer the archetype's routing
principle over an application-specific sequence. Tasks named here belong in the
development/regression set, not in a held-out generalization set.

## Archetypes

| Archetype | First probe | Preferred channel | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Chromium/Edge/Chrome | `apps`, then window scope | AX for page and chrome; GUI only for pixels | Title, URL, tab state, page text | Address bar often a ref; Ctrl+L works; page trees are rich |
| Electron apps | `apps`, targeted `find` | AX for readable state; GUI for actions; else the web version | Window title, timecode/visible state | Empty or non-addressable AX plus a black video surface means GUI is required |
| Native Win32/UIA apps | `apps`, `observe` root | AX | Value/state readback | Dialogs are separate windows; menus are transient |
| Office/LibreOffice | `apps`, find menu/dialog refs | AX fields/dialogs; GUI zoom for formatting | Parsed file or reopened document | Toolbar items may lack names; use menus and shortcuts |
| Qt/Java apps | `apps` after correct launch env | AX when exposed, else GUI | Visible state | May need a restart or toolkit env var |
| Canvas/drawing | `apps`, screenshot | GUI drag/zoom; AX for menus | Pixels and saved file | No semantic targets; verify visually |
| Terminals | `apps`, observe content | AX text tree; type/keys | Output text | Prefer AX over GUI; avoid clipboard assumptions |
| File managers | `apps`, find by name | AX; shell for operations | Filesystem readback | Shell is usually better unless the UI itself is required |
| Multi-window/dialogs | `apps`, then `find` | AX `wait` window/query | Window inventory and state | Close the last window last; re-find after replacement |

## Recipes

### 1. Browser search and play

- Outcome-only: navigate directly to the known target URL; assert the media
  element state and title.
- Explicit UI path: new window (Ctrl+N) -> type the site URL in the address bar
  -> wait for the window title -> find the search field -> type the query ->
  Enter -> wait/query the first result -> click it -> assert playback text or
  player state.
- On Windows, split the Ctrl+N / address-bar click and the text step into
  separate calls; a batch that follows click/keypress with type or
  document-input set_value stops before the text step. Other platforms may
  batch click -> wait -> type.
- On Windows, type and text submit go in a separate call after clicking the
  field; confirm focus first if the effect line is ambiguous.
- Evidence: tab/window title, "playing" text or progress value, not the click.
- If pixels cannot prove playback (for example a black video surface), use
  exposed media state, accessibility text, or audio/progress evidence; if none
  exists, say visual proof is unavailable instead of claiming success. Probe a
  documented app/browser endpoint once, then switch channels.

### 2. Edit and save an open document

- Confirm the app owns the file and whether it has unsaved changes.
- AX for text fields and menus; `select` before `set_value` when replacing.
- Save through the app (Ctrl+S or Save As); answer overwrite dialogs explicitly.
- When the target holds unsaved changes, confirm before overwriting.
- Check or create the destination folder before Save As; answer format
  confirmations explicitly. Know the format's semantics: CSV stores displayed
  values, not formulas, so verify the parsed artifact accordingly.
- On Windows save dialogs, a full path typed into the file-name box may not
  retarget the save; navigate to the folder or verify the actual path on disk.
- Verify by parsing the saved file or reopening it, not by the save click.
- If the app cannot reach a property, save and close, edit with a library,
  parse the result, and reopen only if the task requires the open view.

### 3. Change a setting

- Prefer the settings UI via AX; read the current value first.
- Change it, then reread the effective value (or inspect the config file) as
  evidence.
- Edit config directly only when the app is closed or known to reread it;
  otherwise the running app may overwrite the change.

### 4. File operation

- If no app holds the file open, use the shell: preview, mutate, verify with a
  directory listing or parse.
- Use the file manager only when the visible UI is part of the requirement.
- Never delete recursively without previewing the resolved target.

### 5. Batch data entry

- Select the exact range/field, then `set_value`; read the result back.
- Keep one window per `act`; split before a window change or a dependent state.
- Do not mix pointer input and text in one Windows batch.

### 6. Canvas drag and zoom

- Take one screenshot; zoom to read small text, convert zoom pixels to frame
  pixels; drag with a path, not a series of clicks.
- Verify by a new screenshot or the saved artifact; pixel change is the only
  evidence GUI can give.

### 7. GUI-only application

- `apps` still lists it; AX `activate`/`close`/window waits still work.
- Operate content with GUI; use keyboard shortcuts where known.
- If the AX tree is empty and video is black, expect GUI-only and avoid
  repeated tree reads.
- A Chromium/Electron app can expose a large read-only tree: text and `/value`
  are present, but nodes are `addressable=false` and the window has no action
  ref. Read state with a targeted `find` (for example the timecode) and act
  through GUI.
- Full `observe` of such a tree can be thousands of bytes; prefer `find`
  queries that return only the field you need.
- For an outcome-only playback goal, an already-exposed debugging/media
  endpoint (one probe) or the web version in the existing browser session may
  be simpler; never start another browser or profile.

### 8. Slow dialog or long operation

- `wait` for the window/query with a bounded timeout; then read once.
- A `wait_timeout` is not proof of failure; inspect before retrying.
- Do not stack waits or poll with screenshots when a query wait can answer.

### 9. Occluded or shared-desktop target

- Move or minimize the occluder once; activate the target; prefer
  type-with-ref over clicking covered coordinates.
- `point_owner_mismatch` means the pointer belongs elsewhere; do not retry the
  same click. Re-read, re-plan, or use the keyboard.
- If focus keeps moving, stop and report instead of fighting the desktop.
