"""
Orchestrator — coordinates all watchers and the Claude Code processing loop.

Responsibilities:
- Launch and supervise watcher processes
- Watch /Approved folder and trigger Claude actions
- Schedule periodic tasks (daily briefing, triage)

Usage:
    python orchestrator.py

    # Dry run (no external actions, just logs):
    DRY_RUN=true python orchestrator.py

Requires:
    pip install watchdog python-dotenv schedule
"""

import os
import sys
import json
import time
import logging
import subprocess
import threading
from pathlib import Path
from datetime import datetime

import schedule
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

load_dotenv()

VAULT_PATH = Path(os.getenv("VAULT_PATH", Path(__file__).parent / "AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(VAULT_PATH / "Logs" / "orchestrator.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("Orchestrator")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log_action(action_type: str, details: dict):
    log_file = VAULT_PATH / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": action_type,
        "actor": "orchestrator",
        "dry_run": DRY_RUN,
        **details,
    }
    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    logs.append(entry)
    log_file.write_text(json.dumps(logs, indent=2), encoding="utf-8")


def run_claude_skill(skill_name: str):
    """Invoke a Claude Code agent skill via CLI."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would invoke skill: /{skill_name}")
        return
    logger.info(f"Invoking Claude skill: /{skill_name}")
    result = subprocess.run(
        ["claude", f"/{skill_name}"],
        cwd=str(VAULT_PATH.parent),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error(f"Skill {skill_name} failed: {result.stderr}")
    else:
        logger.info(f"Skill {skill_name} completed.")
    log_action("skill_invoked", {"skill": skill_name, "exit_code": result.returncode})


# ---------------------------------------------------------------------------
# Approved folder watcher — triggers action when human approves something
# ---------------------------------------------------------------------------

class ApprovedFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix == ".md":
            logger.info(f"Approval detected: {path.name}")
            self._handle_approval(path)

    def _handle_approval(self, approval_file: Path):
        content = approval_file.read_text(encoding="utf-8")
        if "action: send_email" in content:
            if DRY_RUN:
                logger.info(f"[DRY RUN] Would send email per: {approval_file.name}")
            else:
                logger.warning("Email MCP not yet configured — Silver tier feature.")
        elif "action: payment" in content:
            logger.warning("Payment actions require human execution — never auto-approved.")
        else:
            logger.info(f"Unknown action type in {approval_file.name} — skipping.")

        # Move to Done
        done_path = VAULT_PATH / "Done" / approval_file.name
        approval_file.rename(done_path)
        logger.info(f"Moved {approval_file.name} → /Done")
        log_action("approval_processed", {"file": approval_file.name})


# ---------------------------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------------------------

def scheduled_triage():
    logger.info("Running scheduled triage...")
    run_claude_skill("triage-needs-action")


def scheduled_process_inbox():
    logger.info("Running scheduled inbox processing...")
    run_claude_skill("process-inbox")


def scheduled_daily_briefing():
    logger.info("Running daily briefing generation...")
    run_claude_skill("daily-briefing")


# ---------------------------------------------------------------------------
# Watcher process launcher
# ---------------------------------------------------------------------------

def launch_filesystem_watcher():
    logger.info("Launching filesystem watcher in background thread...")
    watcher_script = Path(__file__).parent / "watchers" / "filesystem_watcher.py"
    if not watcher_script.exists():
        logger.error("filesystem_watcher.py not found.")
        return

    env = os.environ.copy()
    env["VAULT_PATH"] = str(VAULT_PATH)

    proc = subprocess.Popen(
        [sys.executable, str(watcher_script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    def stream_output():
        for line in proc.stdout:
            logger.info(f"[FileWatcher] {line.rstrip()}")

    threading.Thread(target=stream_output, daemon=True).start()
    logger.info(f"Filesystem watcher started (PID {proc.pid})")
    return proc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    logger.info("=" * 60)
    logger.info("AI Employee Orchestrator starting")
    logger.info(f"Vault: {VAULT_PATH}")
    logger.info(f"Dry Run: {DRY_RUN}")
    logger.info("=" * 60)

    if DRY_RUN:
        logger.warning("DRY_RUN=true — no external actions will be taken.")

    # Ensure log dir exists
    (VAULT_PATH / "Logs").mkdir(parents=True, exist_ok=True)

    # Launch filesystem watcher
    fs_proc = launch_filesystem_watcher()

    # Watch /Approved folder
    approved_dir = VAULT_PATH / "Approved"
    approved_dir.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    observer.schedule(ApprovedFolderHandler(), str(approved_dir), recursive=False)
    observer.start()
    logger.info(f"Watching /Approved for human approvals: {approved_dir}")

    # Schedule recurring tasks
    schedule.every(15).minutes.do(scheduled_triage)
    schedule.every(30).minutes.do(scheduled_process_inbox)
    schedule.every().day.at("08:00").do(scheduled_daily_briefing)

    logger.info("Scheduler active. Tasks: triage every 15m, process every 30m, briefing at 08:00.")

    # Run an initial triage immediately
    scheduled_triage()

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Shutting down orchestrator...")
        observer.stop()
        if fs_proc:
            fs_proc.terminate()
    observer.join()


if __name__ == "__main__":
    main()
