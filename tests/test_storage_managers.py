import tempfile
import unittest
from pathlib import Path

from utils.analysis_manager import AnalysisManager
from utils.feedback_manager import FeedbackManager


class StorageManagerTests(unittest.TestCase):
    def test_analysis_manager_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AnalysisManager(temp_dir)
            analysis_id = manager.save_analysis(
                "user@example.com",
                {
                    "score_one": {"total_match_score": 82},
                    "score_two": {"total_qualification_score": 76}
                },
                {"matched_skill_count": 3}
            )

            record = manager.get_record(analysis_id)
            self.assertIsNotNone(record)
            self.assertEqual(record["user_email"], "user@example.com")
            self.assertEqual(record["diagnostics"]["matched_skill_count"], 3)

    def test_feedback_manager_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            feedback_path = Path(temp_dir) / "feedback.json"
            manager = FeedbackManager(str(feedback_path))
            feedback_id = manager.add_feedback(
                "user@example.com",
                "general",
                "Useful results page",
                {"source_page": "profile"}
            )

            items = manager.get_user_feedback("user@example.com")
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["feedback_id"], feedback_id)
            self.assertEqual(items[0]["metadata"]["source_page"], "profile")


if __name__ == "__main__":
    unittest.main()
