# Contributing

## Design contract

Keep the skill agent-agnostic and the core `SKILL.md` small. Put detailed rules in a focused reference and client-specific behavior in the setup adapter or setup documentation. Do not add another application recipe when a state-ownership, observation, evidence, or recovery rule would solve the broader class.

Preserve the three-layer boundary:

1. **Skill** — task understanding, routing, planning, risk, verification, and recovery.
2. **HCU MCP** — AX/GUI capabilities, refs, guards, and native action results.
3. **OS/application** — real state and native providers.

Do not work around an HCU implementation bug by encoding false tool behavior in the skill. Reproduce it, identify the owning layer, and link the upstream issue when appropriate.

## Rule changes

A behavioral rule change should include:

- a concrete task and initial environment;
- the observed failure or inefficiency, including raw error fields where available;
- why the rule generalizes beyond one application;
- the success oracle and evidence level;
- affected regression cases and at least one untouched holdout case when claiming generalization;
- updates to tests or documentation needed to keep the change reproducible.

Never copy secrets, personal documents, cookies, access tokens, or identifiable desktop screenshots into an issue, test, result, or commit.

## Holdout hygiene

Cases named in `references/scenarios.md` or used to derive a rule are development/regression cases. If a holdout case causes a rule change, promote it to development and create a new untouched holdout. Do not report the modified case as independent validation of that rule.

## Setup changes

`scripts/hcu_setup.py` must remain standard-library-only and safe by default:

- `doctor` and `print-config` must not write files or install anything;
- mutations require interactive confirmation or explicit `--yes` after user approval;
- preserve unrelated configuration and create backups before writes;
- never silently elevate privileges, bypass confirmations, or substitute another MCP implementation;
- use official HCU build/adapter paths and link documentation for new client behavior;
- distinguish build success, MCP handshake, native permissions, and live desktop verification.

Add unit tests for config merging, preservation, backup, failure, and version compatibility. Do not test against a contributor's real user configuration.

## Validation

Before submitting a change, run:

```bash
python3 scripts/validate_skill.py
python3 -m unittest discover -s tests -v
python3 scripts/summarize_results.py evaluations/example-results.json
```

For HCU changes, also run the official smoke test and `computer-use doctor` on each affected platform. Record any untested native behavior explicitly rather than marking it supported by assumption.

## Pull requests

Describe the user-visible problem, the rule or code change, validation performed, remaining platform/client limits, and whether any result files are synthetic. Small, focused changes are preferred over large batches of unrelated application recipes.
