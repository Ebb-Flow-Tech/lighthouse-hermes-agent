---
name: fix
description: "Use when fixing a known bug or issue with a clear symptom. Reproduces, diagnoses root cause, writes failing test, then applies minimal fix."
---

# Fix a Bug or Issue

Fix a bug or issue with a known symptom.

## Step 1: Understand the problem
- Parse the error message, stack trace, or symptom description provided
- Identify the likely files and modules involved
- Read the relevant source code

## Step 2: Reproduce
- Determine how to reproduce the issue (run a test, hit an endpoint, etc.)
- If a test command is obvious, run it to confirm the failure
- If no test exists yet, note that we need one

## Step 3: Diagnose root cause
- Trace the code path from the symptom to the root cause — trace data flow **backward** through the call stack
- Don't just fix the symptom — find WHY it's happening
- Locate similar **working** code and compare implementations
- Check for related issues in nearby code

## Step 4: Write a failing test (RED)
- Before fixing, write a test that reproduces the bug (if one doesn't exist)
- Run it and **watch it fail** — if it passes immediately, the test is wrong
- Confirm it fails for the **right reason** (the actual bug, not a setup issue)

## Step 5: Fix it (GREEN)
- Make the **minimal** change needed to fix the root cause
- Don't refactor unrelated code or add unnecessary improvements

## Step 6: Fresh Verification
You MUST run verification commands **fresh** — do not rely on prior runs or memory:
- Run the new test to confirm it passes
- Run the broader test suite for the affected module to check for regressions:
  - Backend: `cd backend && pytest tests/ -v --tb=short -x`
  - Frontend: `cd frontend && npm run test:run`
- Examine the **full output** and exit status
- No "should work" or "probably fixed" — show evidence or it's not done

**Stop signal**: If the fix doesn't pass after 3 attempts, stop. This likely indicates the root cause diagnosis was wrong — reassess before continuing.

## Step 7: Summary
Provide:
- **Root cause**: The chain of events — why was it broken?
- **Fix**: What did you change and why?
- **Tests**: What tests verify the fix?
- **Related risks**: Any nearby code that might have the same issue
