# Shared task contract

Every nontrivial Dynamic UI RPA task starts with a contract that is engine
neutral. The contract is stored in the authoritative Workspace and is the basis
for routing, execution, verification, recovery, and final completion.

## Required fields

1. **Goal** — the complete user outcome, not a single UI action.
2. **Target objects** — the business objects, files, windows, pages, or records
   that the task must change or verify.
3. **Constraints** — user restrictions, visible-state requirements, explicit
   methods, timing, and data-preservation rules.
4. **Preconditions** — required login state, open windows, files, permissions,
   and cleanup expectations.
5. **Risk level** — `R0`, `R1`, or `R2`.
6. **Success oracle** — the minimum independent evidence that proves the user
   outcome, not merely that an action was accepted.
7. **State owners** — which engine owns each piece of required truth.
8. **Termination policy** — what counts as completed, safe-stopped, blocked,
   failed, or aborted.

If any field is missing and the gap could change the target, payload, risk, or
success check, observe or ask before acting.

## Contract rules

- The contract is task-level. Do not create a new contract when switching
  Browser and Desktop; update the same Workspace instead.
- The method matters. If the user explicitly requires a visible UI path or a
  specific engine, honor it unless it is impossible or unsafe.
- Outcome-only requests may use any legal route that satisfies the success
  oracle. Classify each stage's oracle as process or outcome at plan time:
  outcome-only stages take the shortest programmatic route (data API, direct
  file write, direct URL), and a UI engine is used only when the process itself
  is contracted or the oracle needs live UI state.
- The success oracle must be independently checkable. Prefer an artifact,
  business object, external receipt, or persisted file over a UI click
  acknowledgment.
- Do not weaken the success oracle to make a step easier.
- Do not treat a partial stage completion as task completion.

## Workspace mapping

Store the contract in `task` and `lifecycle`:

- `task.goal`, `task.constraints`, `task.success_criteria`, and
  `task.risk_level`.
- `lifecycle.status`, `lifecycle.current_phase`, and terminal state.
- Step and stage success conditions derive from the contract.
- `result.verification_summary` must reference the same success oracle.

## Engine-specific contracts

This file defines only the shared contract. Engine-specific execution
contracts remain separate:

- Browser-specific observation and action rules live in
  `references/browser-workflow.md` and the current ego-browser guide.
- Desktop-specific AX/GUI, refs, batching, waits, and platform rules live in
  `references/contract.md`, `references/platforms.md`, and the HCU skill.

## Completion

A task is completed only when:

1. The user goal is satisfied.
2. Every required step is completed or validly skipped.
3. Every required mutation is confirmed or safely resolved.
4. The success oracle is independently verified.
5. No critical `unknown` side effect remains.
6. The final Workspace state is persisted and re-read successfully.
