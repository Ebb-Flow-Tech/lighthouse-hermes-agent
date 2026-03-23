---
name: debug
description: "Use when debugging an issue where the cause is unknown — unexpected behavior, test failures, errors without obvious source. Enforces root cause investigation before any fix attempts."
---

# Debug an Unknown Issue

Debug an issue where the cause is unknown.

**Iron rule: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

## Phase 1: Root Cause Investigation
- Parse any error messages, logs, stack traces, or symptoms provided
- Identify the system boundary where the problem manifests (frontend, backend, database, external service)
- Read the relevant source files
- Trace data flow **backward** through the call stack to find the original source
- Check for recent changes: `git log --oneline -10 -- <relevant-files>`
- If multiple independent failures exist (3+), consider dispatching parallel agents — one per problem domain — using the Agent tool

## Phase 2: Pattern Analysis
- Locate similar **working** code in the codebase
- Compare implementations completely — identify ALL differences
- Understand dependency chains that could cause cascading failures
- Check for common pitfalls: missing awaits, wrong types, stale state, race conditions, N+1 queries

## Phase 3: Hypotheses & Testing
List 2-4 plausible root causes ranked by likelihood. For each:
- What would cause this symptom?
- How can we confirm or rule it out?

Present these hypotheses and ask if I have any additional context before investigating.

Then test hypotheses systematically:
- Make **minimal** changes — test ONE variable at a time
- Run targeted tests if available
- Report findings as you go: which hypotheses were ruled out and why

**Stop signal**: If 3+ fix attempts have failed, stop. This likely indicates an architectural issue — discuss with the user before continuing.

## Phase 4: Fix Implementation
- Write a **failing test** that reproduces the bug before writing any fix code
- Run it to confirm it fails for the right reason (RED)
- Implement the **minimal** fix addressing the root cause (GREEN)
- Run the broader test suite for the affected module:
  - Backend: `cd backend && pytest tests/ -v --tb=short -x`
  - Frontend: `cd frontend && npm run test:run`

## Phase 5: Fresh Verification
Before claiming the fix is done, you MUST:
1. Run the verification command **fresh** (not from memory or prior runs)
2. Examine the **full output** and exit status
3. Confirm the output actually supports the claim
- No "should work" or "probably fixed" — evidence or it didn't happen

## Summary
Provide:
- **Root cause**: The chain of events that caused the bug
- **Fix**: What you changed and why
- **Tests**: What tests verify the fix
- **Related risks**: Any nearby code that might have the same issue

## Red Flags — Stop If You Catch Yourself:
- Proposing a solution before investigating
- Attempting multiple fixes simultaneously
- Adding try/catch or error suppression as a "fix"
- Making speculative changes without understanding WHY
- Skipping the failing test step
- If you hit a dead end after 2-3 attempts, stop and share what you've learned so we can redirect

## Supporting Techniques
Available in this directory:
- `root-cause-tracing.md` — Trace bugs backward through call stack to find original trigger
- `defense-in-depth.md` — Add validation at multiple layers after finding root cause
- `condition-based-waiting.md` — Replace arbitrary timeouts with condition polling
