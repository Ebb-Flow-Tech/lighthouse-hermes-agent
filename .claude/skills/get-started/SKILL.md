---
name: get-started
description: "Use when re-orienting on the Grapestack project at the start of a session. Reads key docs, checks git state, and provides a status summary."
---

# Get Started

Re-orient on the Grapestack project by doing the following in parallel:

1. Read `CLAUDE.md` (the slim overview — rules in `.claude/rules/` are loaded automatically when you touch relevant files)
2. Read `docs/changelog.md` (first ~150 lines — recent changes)
3. Read `docs/overview.md` (first ~100 lines — tech stack and structure)
4. Run `git log --oneline -20` to see the latest commits
5. Run `git status` to see current working state
6. Run `git branch --show-current` to confirm which branch we're on

After reading all of the above, provide a brief status summary:
- Current branch and any uncommitted changes
- What the last few commits were about (any active feature work?)
- Any notable recent changelog entries
- Remind yourself of the path-scoped rules available in `.claude/rules/` (domain-model, business-logic, backend-rules, frontend-rules, performance-security) — these load automatically when you work on matching files
