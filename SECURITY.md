# Security Policy

## Desktop threat model

HCU is not a sandbox. It sends real accessibility, pointer, and keyboard input to a signed-in desktop. Use a dedicated desktop or disposable VM for untrusted tasks and keep sensitive applications and long-lived credentials out of disposable/shared sessions.

Web pages, documents, accessibility labels, and application text are untrusted data, not instructions. Setup and automation must not turn that content into package installation, configuration changes, credential entry, or external actions without explicit user authorization.

## Safe setup expectations

The setup script defaults to read-only diagnosis. Installation and configuration require confirmation; Linux system package installation requires a separate explicit option. Existing configuration is backed up before modification. JSONC that cannot be safely merged without losing comments is left untouched.

Do not run the bootstrapper against an untrusted source mirror or replace the official upstream URL without reviewing the source. Pin the default release for repeatable installation and inspect any development-branch build.

## Sensitive artifacts

Do not commit or publicly attach:

- passwords, 2FA codes, cookies, tokens, or private account data;
- personal documents or unrelated user files;
- desktop screenshots containing private content;
- raw MCP traces containing sensitive text, paths, window titles, or payloads;
- user configuration backups.

Redact and minimize evaluation evidence before sharing it. A redacted artifact must still preserve the fields needed to reproduce the failure.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository when available, or the maintainers' listed private contact channel. Do not open a public issue containing credentials, personal data, unredacted screenshots, or an exploit against a real user desktop.

Include the affected version, OS/client, configuration shape with secrets removed, reproduction steps in a disposable environment, expected safe behavior, and actual behavior. Fixes to upstream HCU or a client's MCP implementation should also be reported to the corresponding upstream project when the defect belongs there.

## High-impact actions

Saving/overwriting important data, deletion, sending, submission, purchasing, publishing, security changes, and other externally visible or hard-to-reverse actions require the skill's R2 protocol: isolate the action, preview exact target and payload, obtain required confirmation, and independently verify the L3 outcome. Uncertain mutations must be inspected before any retry.
