# Platform notes

## Common

- One provider per desktop; refs are session-scoped.
- The GUI image is scaled to fit 1366x768 and coordinates map per axis from the
  returned image; a frame lease is checked before every coordinate action.
- Input delivery and selection support differ by platform. Verify resulting
  state; never assume a key or text arrived.

## Windows

- C#/.NET 8 provider (FlaUI UIA3 plus Win32); Windows 10/11; requires an
  unlocked interactive session and a matching integrity level. The provider
  runs as the MCP user. PowerShell 7+ is only needed to build.
- Text is delivered as synchronous Unicode messages, not via the clipboard.
  Budget 15 s total and 5 s per message. Receivers can ignore or mishandle it;
  verify the resulting value.
- **Text-after-input guard**: an AX batch stops before `type` or a
  document-input `set_value` that follows `click`, `scroll`, or `keypress`.
  The earlier input was emitted; text effects are unknown and the response says
  so. Semantic Value/RangeValue writes remain allowed after a click. The guard
  is per call: an intervening wait does not reset it, only a new call does.
  Confirm focus or selection with a fresh observation, then send text in a
  separate call. A GUI batch stops before a non-empty `type` that follows any
  mouse or keyboard input.
- Selection: whole text or one unique match through UIA TextPattern; the
  readback must be complete. Duplicate or missing text fails before input. A
  readback is not the application's callback or cached state.
- UIA visibility can differ from pixels: reobserve instead of forcing a stale
  or offscreen target.
- Coordinate ownership failures surface as `runtime_error` with inner
  `point_owner_mismatch` or `coordinate_target_unverified`. Read
  `input_emitted`; in observed runs the click was refused before dispatch, but
  do not assume it. Do not retry the same click, and a fresh ref for the same
  covered point does not fix ownership: take a screenshot, inspect covering
  windows, or use type-with-ref/keyboard.
- Launch through the Start menu or a shell; confirm the window with `apps`.

## macOS

- Swift provider: AXUIElement, CoreGraphics, ScreenCaptureKit; macOS 14+.
  Grant Accessibility and Screen Recording to the signed provider bundle in
  the signed-in session.
- Permissions are bound to the bundle identity; a change to it (for example
  replacing or re-signing the executable) resets them. Regrant, then restart
  the provider.
- Selection: whole text or one unique match with a writable AX selection
  range; exact readback. Cross-element ranges are rejected.
- Incomplete enumeration or unreadable titles return an error. Missing
  evidence does not prove a close. A window without a unique native handle can
  be visible by title but has no actionable ref.
- Closing the last document can remove the window before capture, leaving
  `effect_unknown`; inspect with a fresh read.
- Some window and input operations use private SkyLight SPI; treat them as
  implementation, not a public contract.
- Launch with `open -a APP`; reuse an existing instance and verify its window.

## Linux

- Python provider embedded in the MCP executable: AT-SPI2, X11, XTest; requires
  an X11 session and the relevant distro packages. Accessibility is switched on
  automatically.
- Apps that were already running before the provider first enabled
  accessibility may need a restart to expose a tree.
- Toolkit matrix: GTK is visible; Qt older than 5.15 needs
  `QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1`; Java needs the ATK wrapper; Firefox
  needs a restart or new profile and may show a dialog; Chromium/Electron need a
  restart after the provider starts.
- Windows without a tree (Blender, REAPER, custom canvases) still appear in
  `apps`; AX can activate/close/wait, GUI operates their content.
- LibreOffice: the VCL bridge is enabled by `SAL_FORCE_IACCESSIBLE2=1` (24.8)
  or is automatic (25.2+); the GTK VCL plugin comes from
  `SAL_USE_VCLPLUGIN=gtk3`. Start it after setting these; a running instance
  keeps its environment.
- Launch with `setsid -f` so a wrapper does not outlive its window. Pass
  `DISPLAY`, `XAUTHORITY`, `XDG_RUNTIME_DIR`, and `DBUS_SESSION_BUS_ADDRESS`.
- Text: AX writes through accessibility; the keyboard fallback goes via IBus
  or the X keymap and is limited to 500 non-ASCII characters per input, about
  35 ms per character, no clipboard. The 500-character limit is for the
  fallback, not the accessibility path. Verify.
- A modal dialog can make activation of the window behind it fail with
  `window_blocked`; answer or close the dialog.
- GUI uses root pixels (`GDK_SCALE=1`); image capture may fall back to raw
  pixels. `apps` may report incomplete coverage; windows without a tree are
  declared GUI-only.
