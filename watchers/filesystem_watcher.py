"""
File System Watcher — monitors the /Inbox folder for new files and
moves them to /Needs_Action with a metadata .md sidecar for Claude to process.

Usage:
    python watchers/filesystem_watcher.py

Requires:
    pip install watchdog
"""

import shutil
import sys
from pathlib import Path
from datetime import datetime

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from watchers.base_watcher import BaseWatcher, logging

PRIORITY_KEYWORDS = {
    "p1": ["urgent", "asap", "emergency", "deadline", "payment due", "overdue"],
    "p2": ["invoice", "payment", "contract", "important", "review"],
}


def detect_priority(filename: str, content: str = "") -> str:
    text = (filename + " " + content).lower()
    for keyword in PRIORITY_KEYWORDS["p1"]:
        if keyword in text:
            return "P1-Urgent"
    for keyword in PRIORITY_KEYWORDS["p2"]:
        if keyword in text:
            return "P2-High"
    return "P3-Normal"


class InboxEventHandler(FileSystemEventHandler):
    def __init__(self, watcher: "FileSystemWatcher"):
        self.watcher = watcher
        self.logger = logging.getLogger("InboxEventHandler")

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        # Ignore hidden files and temp files
        if source.name.startswith(".") or source.suffix in (".tmp", ".part"):
            return
        self.logger.info(f"New file detected: {source.name}")
        self.watcher.create_action_file(source)


class FileSystemWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=5)
        self.inbox = self.vault_path / "Inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.processed = set()

    def check_for_updates(self) -> list:
        """Scan inbox for any files not yet processed (fallback poll)."""
        new_files = []
        for f in self.inbox.iterdir():
            if f.is_file() and f not in self.processed and not f.name.startswith("."):
                new_files.append(f)
        return new_files

    def create_action_file(self, source: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in source.stem)
        dest_name = f"FILE_{safe_stem}_{timestamp}{source.suffix}"
        dest = self.needs_action / dest_name

        # Read a snippet for priority detection (text files only)
        snippet = ""
        if source.suffix.lower() in (".txt", ".md", ".csv", ".json"):
            try:
                snippet = source.read_text(encoding="utf-8", errors="ignore")[:500]
            except Exception:
                pass

        priority = detect_priority(source.name, snippet)

        # Copy file to Needs_Action
        shutil.copy2(source, dest)
        self.processed.add(source)

        # Create metadata sidecar
        meta_path = self.needs_action / f"FILE_{safe_stem}_{timestamp}.md"
        meta_path.write_text(
            f"""---
type: file_drop
original_name: {source.name}
source_path: {source}
size_bytes: {source.stat().st_size}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

## File Received: {source.name}

A new file has been dropped into the Inbox and copied to Needs_Action.

**Priority:** {priority}
**Size:** {source.stat().st_size:,} bytes
**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Suggested Actions
- [ ] Review file contents
- [ ] Determine required action
- [ ] Create Plan.md if multi-step work is needed
- [ ] Move to /Done when complete

## Snippet
```
{snippet[:300] if snippet else "(binary or empty file)"}
```
""",
            encoding="utf-8",
        )

        self.log_action(
            "file_detected",
            {
                "original": source.name,
                "action_file": meta_path.name,
                "priority": priority,
            },
        )
        return meta_path

    def run_with_watchdog(self):
        """Run using watchdog observer for real-time detection."""
        handler = InboxEventHandler(self)
        observer = Observer()
        observer.schedule(handler, str(self.inbox), recursive=False)
        observer.start()
        self.logger.info(f"Watching: {self.inbox}")
        self.logger.info("Drop files into /Inbox to trigger processing.")

        # Also do an initial scan for files already there
        existing = self.check_for_updates()
        for f in existing:
            self.logger.info(f"Processing pre-existing file: {f.name}")
            self.create_action_file(f)

        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Stopping watcher...")
            observer.stop()
        observer.join()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    vault = os.getenv("VAULT_PATH", str(Path(__file__).parent.parent / "AI_Employee_Vault"))
    watcher = FileSystemWatcher(vault)
    watcher.run_with_watchdog()
