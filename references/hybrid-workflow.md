# Hybrid workflow

Hybrid tasks cross Browser and Desktop inside one user goal. They use one
Task Workspace and one ego TaskSpace for the whole task. Switching engines
never restarts the task.

## Execution model

```text
PREPARE → SAVE → SELECT → CHECK → REOBSERVE → CONTINUE
```

1. **PREPARE**: decide that the current engine cannot or should not continue.
2. **SAVE**: write verified steps, pending action, and blockers to the
   Workspace.
3. **SELECT**: choose the target engine and update the active stage.
4. **CHECK**: confirm the target engine is ready.
5. **REOBSERVE**: observe the target environment before acting.
6. **CONTINUE**: resume from the last verified semantic state.

## Handoff rules

- Handoff is stage-level, not click-level.
- Record the reason, last verified state, pending action, and result.
- The receiving engine must understand the task from the Workspace, not from
  a repeated user explanation.
- Do not re-execute completed and verified steps.
- Do not carry Browser refs, HCU refs, `targetId`, GUI frames, or old
  coordinates across engines.
- Do not let Browser and Desktop write the same UI state concurrently.
- Returning to Browser resumes the original ego TaskSpace and takes a fresh
  snapshot before acting.

## Workspace continuity

- One user task → one Workspace.
- One Browser goal → one ego TaskSpace.
- Multiple handoffs still use the same Workspace and increment `revision`.
- Stage and step IDs remain stable across engine changes.
- A completed step keeps its verification evidence and is not repeated merely
  because the engine changed.

## Failure handling

If a handoff fails:

1. Preserve the Workspace and the last verified state.
2. Mark the current stage or step `blocked` or `failed` as appropriate.
3. Record why the target engine is unavailable.
4. Do not repeat a completed side effect from the previous engine.
5. Wait for recovery conditions or stop safely.

If a step result is `unknown`:

1. Re-observe the target environment.
2. Determine whether the side effect already occurred.
3. Only then decide whether a retry, a different route, or a stop is safe.

## Completion

A Hybrid task is completed only when:

- Every stage has a verified terminal state.
- Every mutation is confirmed or safely resolved.
- The final business result is independently verified.
- The Workspace is persisted, re-read, and marked completed.
- The ego TaskSpace is finished exactly once at the end of the whole goal.
