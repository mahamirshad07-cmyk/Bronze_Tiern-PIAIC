# Personal AI Employee — Bronze Tier

> **Hackathon:** Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026
> **Tier:** Bronze (Foundation)
> **Author:** Roy Yosef

A local-first autonomous AI Employee built with Claude Code and Obsidian. It monitors your inbox, triages incoming files by priority, creates action plans, and keeps a live dashboard — all without manual intervention.

---

## Demo

**Full cycle in action:**
1. Drop any file into `/Inbox`
2. Watcher detects it in real time and classifies priority (P1–P4)
3. Metadata action file created in `/Needs_Action`
4. Claude Code processes it, creates a plan, updates `Dashboard.md`
5. Task moved to `/Done` — visible instantly in Obsidian

---

## Architecture

```
┌─────────────────────────────────────────┐
│           EXTERNAL INPUT                │
│   Files dropped into /Inbox             │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         PERCEPTION LAYER                │
│   filesystem_watcher.py (watchdog)      │
│   Detects new files → writes .md        │
│   sidecars to /Needs_Action             │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         OBSIDIAN VAULT (Local)          │
│  /Inbox  /Needs_Action  /Done  /Plans   │
│  /Logs   /Pending_Approval  /Approved   │
│  Dashboard.md  Company_Handbook.md      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│         REASONING LAYER                 │
│   Claude Code + Agent Skills            │
│   /process-inbox                        │
│   /triage-needs-action                  │
│   /daily-briefing                       │
└─────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Reasoning Engine | Claude Code |
| Knowledge Base / GUI | Obsidian (local Markdown) |
| Watcher | Python 3.13 + watchdog |
| Orchestration | Python + schedule |
| Agent Skills | Claude Code `.claude/skills/` |

---

## Project Structure

```
E:\Hackathon\
├── AI_Employee_Vault\          # Obsidian vault
│   ├── Dashboard.md            # Live status board
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Business_Goals.md       # KPIs and objectives
│   ├── Inbox\                  # Drop zone for new files
│   ├── Needs_Action\           # Items Claude must process
│   ├── Done\                   # Completed tasks
│   ├── Plans\                  # Claude's step-by-step plans
│   ├── Logs\                   # Audit trail (JSON per day)
│   ├── Pending_Approval\       # Awaiting human approval
│   ├── Approved\               # Human-approved actions
│   └── Rejected\               # Rejected actions
├── watchers\
│   ├── base_watcher.py         # Abstract watcher base class
│   ├── filesystem_watcher.py   # Working watcher (Bronze tier)
│   └── gmail_watcher.py        # Gmail watcher (Silver tier)
├── .claude\
│   └── skills\
│       ├── process-inbox.md        # Triage and process Needs_Action
│       ├── triage-needs-action.md  # Fast priority sort
│       └── daily-briefing.md       # Morning CEO briefing
├── orchestrator.py             # Coordinates watchers + scheduler
├── pyproject.toml              # UV project config
├── requirements.txt            # pip dependencies
├── setup.ps1                   # One-command Windows setup
├── .env.example                # Environment variable template
└── .gitignore                  # Excludes secrets and logs
```

---

## Setup

### Prerequisites
- Python 3.13+
- Claude Code (active subscription)
- Obsidian v1.10.6+

### Install

```powershell
# Clone the repo
git clone <your-repo-url>
cd Hackathon

# Run setup (installs dependencies, creates .env)
.\setup.ps1
```

Or manually:
```powershell
pip install watchdog python-dotenv schedule
copy .env.example .env
```

### Configure

Edit `.env`:
```env
VAULT_PATH=E:\Hackathon\AI_Employee_Vault
DRY_RUN=true
```

### Open Vault in Obsidian

1. Launch Obsidian
2. Click **Open folder as vault**
3. Select `AI_Employee_Vault\`
4. Open `Dashboard.md` as your home screen

---

## Usage

### Start the Filesystem Watcher

```powershell
python watchers/filesystem_watcher.py
```

### Drop a file into /Inbox

Drag any file into `AI_Employee_Vault\Inbox\` via File Explorer.

The watcher auto-classifies priority:

| Keywords in filename/content | Priority |
|---|---|
| urgent, asap, emergency | P1-Urgent |
| invoice, payment, contract | P2-High |
| *(anything else)* | P3-Normal |

### Run Claude Code Skills

```powershell
cd E:\Hackathon
claude
```

Then inside Claude Code:
```
/process-inbox        # Process all pending items
/triage-needs-action  # Quick priority sort
/daily-briefing       # Generate morning CEO briefing
```

### Run the Full Orchestrator

```powershell
python orchestrator.py
```

Runs the watcher, watches `/Approved` folder, and schedules skills automatically (triage every 15min, process every 30min, briefing at 08:00).

---

## Agent Skills

All AI functionality is implemented as Claude Code Agent Skills in `.claude/skills/`:

| Skill | Trigger | What it does |
|---|---|---|
| `/process-inbox` | Manual or scheduled | Reads Needs_Action, triages, creates plans, updates Dashboard, moves to Done |
| `/triage-needs-action` | Manual or scheduled | Classifies and sorts pending items by priority |
| `/daily-briefing` | Daily at 08:00 | Generates a Morning CEO Briefing markdown file |

---

## Security Disclosure

See [SECURITY.md](SECURITY.md) for full details.

**Summary:**
- No credentials are stored in the vault or committed to git
- `.env` is in `.gitignore` — secrets stay local only
- `DRY_RUN=true` by default — no external actions without explicit opt-in
- All sensitive actions (email send, payments) require human approval via `/Pending_Approval`
- Full audit log written to `/Logs/YYYY-MM-DD.json` for every action taken

---

## Tier Declaration

**Bronze Tier — Foundation**

| Requirement | Status |
|---|---|
| Obsidian vault with Dashboard.md and Company_Handbook.md | ✅ |
| One working Watcher script | ✅ filesystem_watcher.py |
| Claude Code reading from and writing to vault | ✅ |
| Basic folder structure: /Inbox, /Needs_Action, /Done | ✅ |
| All AI functionality as Agent Skills | ✅ 3 skills |
