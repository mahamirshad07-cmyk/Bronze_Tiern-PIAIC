"""
Gmail Watcher — monitors Gmail for unread important messages and creates
action files in /Needs_Action for Claude to process.

Setup:
    1. Go to Google Cloud Console and enable the Gmail API.
    2. Download OAuth credentials as credentials.json into the project root.
    3. Run once interactively to generate token.json:
           python watchers/gmail_watcher.py --auth
    4. Set GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH in your .env file.

Usage:
    python watchers/gmail_watcher.py

Requires:
    pip install google-auth google-auth-oauthlib google-api-python-client
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from watchers.base_watcher import BaseWatcher

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

SENSITIVE_KEYWORDS = [
    "invoice", "payment", "urgent", "contract", "bank", "transfer",
    "password", "reset", "security", "lawsuit", "medical",
]


def detect_priority(subject: str, snippet: str) -> str:
    text = (subject + " " + snippet).lower()
    urgent = ["urgent", "asap", "emergency", "deadline", "overdue", "immediately"]
    high = ["invoice", "payment", "contract", "action required", "important"]
    if any(k in text for k in urgent):
        return "P1-Urgent"
    if any(k in text for k in high):
        return "P2-High"
    return "P3-Normal"


def flag_sensitive(subject: str, snippet: str) -> bool:
    text = (subject + " " + snippet).lower()
    return any(k in text for k in SENSITIVE_KEYWORDS)


class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str, token_path: str):
        super().__init__(vault_path, check_interval=120)
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.processed_ids: set = self._load_processed_ids()
        self.service = self._build_service()

    def _load_processed_ids(self) -> set:
        cache = self.vault_path / ".gmail_processed.json"
        if cache.exists():
            try:
                return set(json.loads(cache.read_text(encoding="utf-8")))
            except Exception:
                pass
        return set()

    def _save_processed_ids(self):
        cache = self.vault_path / ".gmail_processed.json"
        cache.write_text(json.dumps(list(self.processed_ids)), encoding="utf-8")

    def _build_service(self):
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                self.token_path.write_text(creds.to_json(), encoding="utf-8")
            return build("gmail", "v1", credentials=creds)
        except ImportError:
            self.logger.error(
                "Google API libraries not installed. Run: "
                "pip install google-auth google-auth-oauthlib google-api-python-client"
            )
            return None

    def check_for_updates(self) -> list:
        if not self.service:
            return []
        result = self.service.users().messages().list(
            userId="me", q="is:unread is:important", maxResults=20
        ).execute()
        messages = result.get("messages", [])
        return [m for m in messages if m["id"] not in self.processed_ids]

    def create_action_file(self, message: dict) -> Path:
        msg = self.service.users().messages().get(
            userId="me", id=message["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "(No Subject)")
        sender = headers.get("From", "Unknown")
        date = headers.get("Date", "")
        snippet = msg.get("snippet", "")

        priority = detect_priority(subject, snippet)
        is_sensitive = flag_sensitive(subject, snippet)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.needs_action / f"EMAIL_{message['id']}_{timestamp}.md"
        filepath.write_text(
            f"""---
type: email
message_id: {message['id']}
from: {sender}
subject: {subject}
date: {date}
received: {datetime.now().isoformat()}
priority: {priority}
sensitive: {str(is_sensitive).lower()}
status: pending
requires_approval: {str(is_sensitive).lower()}
---

## Email: {subject}

**From:** {sender}
**Date:** {date}
**Priority:** {priority}
{"**⚠️ SENSITIVE — Requires Human Approval before any action.**" if is_sensitive else ""}

## Snippet
> {snippet}

## Suggested Actions
- [ ] Review and categorize
- [ ] Draft reply (if needed) → move draft to /Pending_Approval
- [ ] Archive or flag in Gmail
- [ ] Move this file to /Done when complete
""",
            encoding="utf-8",
        )

        self.processed_ids.add(message["id"])
        self._save_processed_ids()
        self.log_action(
            "email_detected",
            {
                "message_id": message["id"],
                "subject": subject,
                "from": sender,
                "priority": priority,
                "sensitive": is_sensitive,
                "action_file": filepath.name,
            },
        )
        return filepath


def authenticate(credentials_path: str, token_path: str):
    """Run OAuth flow interactively to generate token.json."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    Path(token_path).write_text(creds.to_json(), encoding="utf-8")
    print(f"Token saved to {token_path}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Gmail Watcher")
    parser.add_argument("--auth", action="store_true", help="Run OAuth flow to generate token")
    args = parser.parse_args()

    vault = os.getenv("VAULT_PATH", str(Path(__file__).parent.parent / "AI_Employee_Vault"))
    creds = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    token = os.getenv("GMAIL_TOKEN_PATH", "token.json")

    if args.auth:
        authenticate(creds, token)
    else:
        watcher = GmailWatcher(vault, creds, token)
        watcher.run()
