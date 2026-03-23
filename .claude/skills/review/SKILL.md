---
name: review
description: "Use when reviewing code changes for quality, correctness, and adherence to project conventions — uncommitted changes, staged changes, or a specific PR."
---

# Review Code Changes

Review code changes for quality, correctness, and adherence to project conventions.

## Step 1: Identify what to review
- If context specifies files or a PR, review those
- Otherwise, review all uncommitted changes: `git diff --stat` and `git diff --cached --stat`
- If no changes exist, check the latest commit: `git log -1 --stat`

## Step 2: Read the changes
- Read the full diff of all changed files
- For each changed file, also read enough surrounding context to understand the change

## Step 3: Review systematically
Evaluate each change against these categories, ordered by severity:

### Critical (blocks merge)
- Bugs: logic errors, off-by-one, null/undefined access, race conditions
- Security: injection, auth bypass, exposed secrets, missing input validation
- Data loss: missing migrations, destructive operations without safeguards
- Breaking changes: API contract violations, removed fields still in use

### Important (should fix)
- Missing tests for new behavior
- Error handling gaps at system boundaries (user input, external APIs)
- Performance: N+1 queries, missing pagination, unbounded loops
- Incorrect types or model mismatches between frontend/backend

### Suggestions (nice to have)
- Naming clarity
- Code organization
- Pattern consistency with existing codebase

## Step 4: Present findings
Format as:
```
### Critical
- [file:line] Description of issue and why it matters

### Important
- [file:line] Description

### Suggestions
- [file:line] Description
```

If no issues found, say so clearly. Don't manufacture problems.

## Step 5: Offer to fix
If critical or important issues were found, ask if I want you to fix them.

## Rules
- Do NOT nitpick style that matches the existing codebase
- Do NOT suggest adding comments, docstrings, or type annotations to unchanged code
- Do NOT flag things as issues when they follow established project patterns
- Focus on correctness and bugs, not personal preferences

## Supporting Files
- `code-reviewer.md` — Agent prompt template for dispatching a code reviewer subagent
