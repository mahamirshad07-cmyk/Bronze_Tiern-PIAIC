# Skill: Process Inbox

Process all pending items in the AI Employee vault's /Needs_Action folder. For each item, triage it, create a plan if needed, and update the Dashboard.

## Steps

1. **Read the handbook** — load `AI_Employee_Vault/Company_Handbook.md` to understand permission boundaries and priority rules.

2. **List all files in /Needs_Action** — find every `.md` file that has `status: pending` in its frontmatter.

3. **For each pending item:**
   a. Read the file and determine:
      - What type of item it is (email, file drop, task, etc.)
      - Its priority (P1–P4)
      - Whether it requires human approval before any action
   b. If `requires_approval: true` — copy the item to `/Pending_Approval/` and add a note explaining what approval is needed. Do NOT take any external action.
   c. If it is a simple informational item — summarize it and mark it done.
   d. If it requires multi-step work — create a `Plans/PLAN_<item_name>_<date>.md` with a checkbox list of steps.
   e. Update the item's frontmatter: change `status: pending` → `status: processed`.

4. **Update Dashboard.md:**
   - Increment "Tasks Processed" counter
   - Add a line to "Recent Activity" with timestamp and brief description
   - Update "Pending in /Needs_Action" count

5. **Move completed items to /Done** — once processed and any required plan is created, move the action file to `/Done/`.

6. **Log the session** — append a JSON entry to `/Logs/<today>.json` with what was processed.

## Rules
- Never send emails, make payments, or post to social media — those require MCP servers (Silver tier).
- Never delete files.
- If an item is ambiguous, leave it in /Needs_Action and write a question in Dashboard.md under a "Clarification Needed" section.
- Always respect priority order: P1 first, then P2, P3, P4.
