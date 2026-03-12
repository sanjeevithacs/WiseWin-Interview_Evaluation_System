import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalysisManager:
    """Stores resume analysis results for history and export."""

    def __init__(self, storage_dir: str = "analysis_history"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save_analysis(self, user_email: str, analysis: Dict[str, Any], diagnostics: Dict[str, Any]) -> str:
        analysis_id = str(uuid.uuid4())
        record = {
            "analysis_id": analysis_id,
            "user_email": user_email,
            "created_at": datetime.now().isoformat(),
            "analysis": analysis,
            "diagnostics": diagnostics,
            "match_score": analysis.get("score_one", {}).get("total_match_score", 0),
            "qualification_score": analysis.get("score_two", {}).get("total_qualification_score", 0),
        }
        self._save_record(analysis_id, record)
        return analysis_id

    def get_record(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        path = self.storage_dir / f"{analysis_id}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_user_history(self, user_email: str, limit: int = 20) -> List[Dict[str, Any]]:
        records = []
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as file:
                    record = json.load(file)
                if record.get("user_email") == user_email:
                    records.append(record)
            except Exception as exc:
                logger.error("Failed to load analysis record %s: %s", path, exc)
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return records[:limit]

    def _save_record(self, analysis_id: str, record: Dict[str, Any]) -> None:
        path = self.storage_dir / f"{analysis_id}.json"
        with open(path, "w", encoding="utf-8") as file:
            json.dump(record, file, indent=2, ensure_ascii=False)
