---
name: ophanim-run-checks
description: Runs the required pytest and ruff checks for Ophanim AI to verify task completion criteria. Use this before claiming a task is done.
---
# Ophanim AI Checks

Before marking any task as complete, you MUST run the verification checks for the repository.

1. **Run Tests**:
   - Command: `pytest`
   - CWD: `c:\Projects\Ophanim_AI\services\ophanim-core`
   - Expectation: All tests must pass. Do not remove or weaken tests to get a passing run.

2. **Run Linter**:
   - Command: `ruff check ophanim tests`
   - CWD: `c:\Projects\Ophanim_AI\services\ophanim-core`
   - Expectation: 0 errors. Fix any linting errors before proceeding.

3. **Verify Git Diff**:
   - Command: `git diff --check`
   - CWD: `c:\Projects\Ophanim_AI`
   - Expectation: No whitespace errors.
