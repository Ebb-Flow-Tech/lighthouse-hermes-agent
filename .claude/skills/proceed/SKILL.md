---
name: proceed
description: "Use when continuing implementation of an existing plan. Finds the plan, assesses progress, and executes remaining tasks using subagent-driven or sequential strategy."
---

# Continue Implementing a Plan

Continue implementing an existing plan.

## Step 1: Find the plan
- Check both `docs/plans/` and `docs/executing/` for available plans
- If multiple plans exist across either folder, list them all and ask which one to continue
- If the user provided a plan name, search both folders for that specific plan
- Plans in `docs/executing/` are actively in progress; plans in `docs/plans/` are ready to start

**When starting a plan from `docs/plans/`**: move the file to `docs/executing/` before beginning work. Create the folder if it doesn't exist.

## Step 2: Assess progress
- Read the plan document fully
- Check git log for recent commits related to the plan: `git log --oneline -15`
- Check `git diff --stat` for any work in progress
- Determine which steps are already complete and which are next

## Step 3: Present status
Give a brief status update:
- **Plan**: [name]
- **Completed**: Steps X, Y, Z
- **Next up**: Step N — [brief description]
- **Remaining**: Steps after that

Ask if I want to proceed with the next step or skip/adjust anything.

## Step 4: Choose execution strategy
Based on the remaining tasks, select the best approach:

### Subagent-driven (for plans with 3+ independent tasks)
When remaining tasks can be worked on independently:
- Dispatch **one Agent per independent task** using the Agent tool
- Each agent gets: task description, file paths, acceptance criteria, test commands
- Launch independent agents **in parallel** (single message, multiple Agent tool calls)
- After each agent completes, review its work:
  1. **Spec compliance**: Does it match the plan's requirements?
  2. **Code quality**: Does it follow codebase patterns and conventions?
- If issues found, fix them before moving on
- A task is only "done" when both reviews pass

**Handling agent status:**
- **DONE**: Proceed to review
- **DONE_WITH_CONCERNS**: Read concerns before review — address if about correctness/scope
- **NEEDS_CONTEXT**: Provide missing context and re-dispatch
- **BLOCKED**: Assess blocker — provide more context, try a more capable model, split the task, or escalate to user

### Sequential (for tightly-coupled tasks)
When tasks depend heavily on each other:
- Implement tasks one by one
- After completing each task, run its verification step
- Mark completed steps in the plan document (checkbox `[x]`)
- Continue to the next step unless blocked

## Step 5: Verify each completed task
Before marking ANY task as complete:
1. Run the verification command specified in the plan **fresh**
2. Examine the **full output** — not just the exit code
3. Confirm the output actually demonstrates the task is done
- No "should work" — evidence or it's not done

## Step 6: Check in
After completing a meaningful chunk of work:
- Summarize what was done
- Show test results
- State what's next
- Ask if I want to continue, pause, or adjust the plan

**Never offer to commit, push, or create a PR.** Do not ask about git operations — that is the user's responsibility.

## Step 7: Mark plan complete
When all non-manual-testing steps are done:
- Move the plan file from `docs/executing/` to `docs/completions/` (create the folder if needed)
- Manual testing steps (steps requiring human interaction, browser testing, or QA sign-off) do **not** block completion — skip them when assessing whether all steps are done

## Supporting Files
- `implementer-prompt.md` — Prompt template for implementer subagents
- `spec-reviewer-prompt.md` — Prompt template for spec compliance review subagents
- `code-quality-reviewer-prompt.md` — Prompt template for code quality review subagents
