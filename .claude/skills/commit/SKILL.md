---
name: commit
description: "Use when generating a commit message for recent changes. Analyzes diffs, checks if docs need updating, and generates a commit message following repo conventions."
---

# Generate a Commit

Look at the latest changes and generate a commit message.

## Step 1: Analyze changes
Run in parallel:
- `git diff --cached --stat` (staged changes)
- `git diff --stat` (unstaged changes)
- `git status --short`
- `git log --oneline -5` (recent commit style)

## Step 2: Doc-sync check
Based on the changes, check if any of these docs need updating:

**If you added/changed models, enums, routes, stores, hooks, or services:**
- Read `CLAUDE.md` and check if counts, entity tables, or architecture descriptions are still accurate
- Update counts (e.g., "35+ modules" -> "36+ modules") and add new entities/enums

**If you added/changed backend domain logic or business rules:**
- Read `.claude/rules/business-logic.md` and check if workflows, batch refs, or business rules need updating

**If you added/changed backend models or migrations:**
- Read `.claude/rules/domain-model.md` and check if the entity table, enums, or relationships need updating

**If you changed notable features or fixed significant bugs:**
- Read `docs/changelog.md` (first ~50 lines) and add an entry under the current version

**If you added new UI patterns or design elements:**
- Check if `docs/design-principles.md` needs updating

**If you changed architecture, infrastructure, routes, services, or deployment config:**
- Read `docs/architecture.md` and check if diagrams, descriptions, or component lists are still accurate
- Read `docs/deployment.md` and check if deployment steps, env vars, or infrastructure details need updating

Only update docs that are actually stale — don't touch docs that are already accurate.

## Step 3: Generate commit message
- Generate a concise commit message following the repo's existing style
- Output the commit message clearly so I can copy it
- Do NOT run git commit or git push — I will do that manually

## Step 4: Summary
Show a brief summary of the suggested commit message and any docs that were updated.
