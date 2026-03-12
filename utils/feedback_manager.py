import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FeedbackManager:
    """Stores product feedback submitted by users."""

    def __init__(self, storage_file: str = "feedback.json"):
        self.storage_file = Path(storage_file)
        if not self.storage_file.exists():
            self.storage_file.write_text("[]", encoding="utf-8")

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.storage_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as exc:
            logger.error("Failed to load feedback: %s", exc)
            return []

    def _save(self, items: List[Dict[str, Any]]) -> None:
        with open(self.storage_file, "w", encoding="utf-8") as file:
            json.dump(items, file, indent=2, ensure_ascii=False)

    def add_feedback(self, user_email: str, category: str, message: str, metadata: Dict[str, Any] | None = None) -> str:
        items = self._load()
        feedback_id = str(uuid.uuid4())
        items.append({
            "feedback_id": feedback_id,
            "user_email": user_email,
            "category": category,
            "message": message,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": datetime.now().isoformat()
        })
        self._save(items)
        return feedback_id

    def get_user_feedback(self, user_email: str, limit: int = 20) -> List[Dict[str, Any]]:
        items = [item for item in self._load() if item.get("user_email") == user_email]
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items[:limit]

    def get_all_feedback(self, limit: int = 100) -> List[Dict[str, Any]]:
        items = self._load()
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items[:limit]

    def set_feedback_status(self, feedback_id: str, status: str) -> bool:
        items = self._load()
        updated = False
        for item in items:
            if item.get("feedback_id") == feedback_id:
                item["status"] = status
                item["updated_at"] = datetime.now().isoformat()
                updated = True
                break
        if updated:
            self._save(items)
        return updated
