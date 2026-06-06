import unittest
from datetime import datetime, timezone

from src.news_collector import NewsCandidate
from src.ranker import _priority_score, _topic_signature


class OfficialReleaseDeduplicationTests(unittest.TestCase):
    def test_fomc_official_and_media_titles_share_signature(self) -> None:
        self.assertEqual(
            _topic_signature("federal reserve issues fomc statement"),
            "fomc-policy-decision",
        )
        self.assertEqual(
            _topic_signature("fed holds rates steady after policy meeting"),
            "fomc-policy-decision",
        )

    def test_bls_official_and_media_titles_share_signature(self) -> None:
        self.assertEqual(
            _topic_signature("cpi for all items rises 0.6% in april"),
            "us-cpi-release",
        )
        self.assertEqual(
            _topic_signature("hot consumer price index report shakes markets"),
            "us-cpi-release",
        )

    def test_stock_prediction_is_penalized(self) -> None:
        factual = NewsCandidate(
            title="Micron reports quarterly earnings",
            url="https://example.com/factual",
            source="Reuters",
            published_at=datetime.now(timezone.utc),
        )
        prediction = NewsCandidate(
            title="Prediction: This AI chip stock will soar after Micron earnings",
            url="https://example.com/prediction",
            source="AOL.com",
            published_at=datetime.now(timezone.utc),
        )

        self.assertGreater(_priority_score(factual), _priority_score(prediction))


if __name__ == "__main__":
    unittest.main()
