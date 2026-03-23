---
name: verify
description: "Use when verifying that recent work is actually complete and correct. Runs fresh verification commands and checks requirements against evidence. No completion claims without proof."
---

# Verify Recent Work

Verify that recent work is actually complete and correct.

**Rule: NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

## Step 1: Identify what to verify
- If context specifies a feature/fix, verify that
- Otherwise, check git log and diff for recent work: `git log --oneline -5` and `git diff --stat`
- Read any related plan in `docs/plans/` or `docs/completions/` to understand the acceptance criteria

## Step 2: Run all verification commands fresh
For each piece of recent work:
1. Identify which command validates the claim (test suite, build, lint, etc.)
2. Execute that command **right now** — do NOT trust prior runs
3. Examine the **full output** and exit status
4. Confirm the output actually supports the claim

Standard verification suite:
- Backend tests: `cd backend && pytest tests/ -v --tb=short`
- Frontend tests: `cd frontend && npm run test:run`
- Frontend build: `cd frontend && npm run build`
- Frontend lint: `cd frontend && npm run lint`

Only run what's relevant to the recent changes.

## Step 3: Check requirements against evidence
For each requirement or acceptance criterion:
- [ ] Is there a test that covers it?
- [ ] Does the test pass (verified just now)?
- [ ] Does the implementation match the spec (not just "tests pass")?

## Step 4: Report
Present findings clearly:
- **Verified**: What passed with evidence (command output)
- **Failed**: What didn't pass, with the actual error
- **Not covered**: Requirements that have no verification

## Rules
- Never use tentative language: "should work", "probably fixed", "looks good"
- Evidence precedes claims — always, no exceptions
- If you can't verify something programmatically, say so explicitly
- Claiming work is complete without verification is dishonesty, not efficiency
