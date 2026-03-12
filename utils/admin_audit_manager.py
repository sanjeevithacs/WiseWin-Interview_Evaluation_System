import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AdminAuditManager:
    """Stores audit records for admin actions."""

    def __init__(self, storage_file: str = "admin_audit.json"):
        self.storage_file = Path(storage_file)
        if not self.storage_file.exists():
            self.storage_file.write_text("[]", encoding="utf-8")

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.storage_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as exc:
            logger.error("Failed to load admin audit log: %s", exc)
            return []

    def _save(self, items: List[Dict[str, Any]]) -> None:
        with open(self.storage_file, "w", encoding="utf-8") as file:
            json.dump(items, file, indent=2, ensure_ascii=False)

    def log(self, admin_email: str, action: str, target: str, metadata: Dict[str, Any] | None = None) -> str:
        items = self._load()
        audit_id = str(uuid.uuid4())
        items.append({
            "audit_id": audit_id,
            "admin_email": admin_email,
            "action": action,
            "target": target,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        })
        self._save(items)
        return audit_id

    def list_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        items = self._load()
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items[:limit]
