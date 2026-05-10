# Security Disclosure

## Credential Handling

- All credentials (API keys, OAuth tokens, passwords) are stored **only** in a local `.env` file
- `.env` is listed in `.gitignore` and is **never committed to git**
- The Obsidian vault contains **no secrets** — only markdown files
- `.env.example` is provided as a safe template with no real values

## Secrets Never Stored In

- Vault markdown files (`Dashboard.md`, `Company_Handbook.md`, etc.)
- Git history
- Log files (`/Logs/YYYY-MM-DD.json`) — logs record action type and metadata only, never credentials or full message bodies

## Dry Run Mode

- `DRY_RUN=true` is the default in `.env.example`
- When enabled, no external actions are taken — all actions are logged only
- Must be explicitly set to `false` to enable live actions

## Human-in-the-Loop (HITL)

All sensitive actions require explicit human approval before execution:

| Action | How approval works |
|---|---|
| Send email | Claude writes to `/Pending_Approval/` — human moves file to `/Approved/` |
| Make payment | Never auto-approved — always requires human execution |
| Post to social media | Draft only — human approves before publish |
| Delete files | Never automated |

The AI Employee will **not** take any of these actions autonomously. It stops at the approval request file.

## Permission Boundaries

| Action | Auto | Requires Approval |
|---|---|---|
| Read/write vault files | ✅ | — |
| Create plans and summaries | ✅ | — |
| Move files within vault | ✅ | — |
| Send emails | ❌ | Always |
| Payments | ❌ | Always |
| Delete files | ❌ | Always |

## Audit Logging

Every action is logged to `/AI_Employee_Vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-05-10T15:42:00Z",
  "action_type": "file_detected",
  "actor": "FileSystemWatcher",
  "dry_run": true,
  "file": "client_b_followup.txt",
  "priority": "P1-Urgent"
}
```

Logs are retained locally and excluded from git.

## Data Privacy

- All data remains **local-first** — nothing leaves your machine unless you explicitly configure an MCP server
- The Obsidian vault is stored on your local filesystem only
- No telemetry or data collection by this project
