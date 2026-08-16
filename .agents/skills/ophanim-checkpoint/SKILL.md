---
name: ophanim-checkpoint
description: Creates the required task checkpoint markdown file in docs/checkpoints/ to document task completion. Use this at the end of an authorized task.
---
# Ophanim AI Task Checkpoint Generator

At the end of an authorized task, you MUST create a checkpoint file to document completion before stopping.

## Checkpoint Format
Create a file at `docs/checkpoints/<TASK-ID>.md` (for example, `docs/checkpoints/UI-R1-T01.md`).
Ensure the file contains the following structure exactly, as defined in `CODEX.md`:

```text
Task ID
Status
Completed at
Objective
Scope delivered
Files changed
Architecture impact
Security impact
Tests and results
Acceptance criteria verification
Migrations/rollback
Known limitations
Open risks/blockers
Recommended next task (informational only)
```

After creating this file, present the completion report to the user and STOP. Do not start the next task automatically.
