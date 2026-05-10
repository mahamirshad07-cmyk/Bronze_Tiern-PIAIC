import time
import logging
import json
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("watcher.log", encoding="utf-8"),
    ],
)


class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ensure_dirs()

    def _ensure_dirs(self):
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder."""
        pass

    def log_action(self, action_type: str, details: dict):
        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": self.__class__.__name__,
            **details,
        }
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logs = []
        logs.append(entry)
        log_file.write_text(json.dumps(logs, indent=2), encoding="utf-8")

    def run(self):
        self.logger.info(f"Starting {self.__class__.__name__} (interval={self.check_interval}s)")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    path = self.create_action_file(item)
                    self.logger.info(f"Created action file: {path.name}")
                    self.log_action("action_file_created", {"file": str(path)})
            except Exception as e:
                self.logger.error(f"Error in watcher loop: {e}", exc_info=True)
            time.sleep(self.check_interval)
