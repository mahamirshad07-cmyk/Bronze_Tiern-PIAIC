# Skill: Triage Needs Action

Quickly scan /Needs_Action and sort items by priority. Do not process them — only classify, sort, and update the Dashboard with the prioritized queue.

## Steps

1. **List all files in `/AI_Employee_Vault/Needs_Action/`** with `status: pending`.

2. **For each file, read its frontmatter** to extract:
   - `type` (email, file_drop, task, etc.)
   - `priority` (P1–P4, or infer from content if missing)
   - `received` timestamp
   - `requires_approval`

3. **Build a prioritized queue** sorted by: P1 → P2 → P3 → P4, and within each tier by `received` (oldest first).

4. **Update Dashboard.md** — replace or create a "## Inbox Queue" section with a table:

```markdown
## Inbox Queue
| Priority | File | Type | Age | Approval? |
|----------|------|------|-----|-----------|
| P1 | ... | ... | ... | Yes/No |
```

5. **Flag any P1 items** by prepending `⚠️ P1-URGENT: ` to their filename (rename the file in place) so they are visually prominent.

## Rules
- Do not move files.
- Do not take any action on the items — triage only.
- If priority cannot be determined, default to P3-Normal.
