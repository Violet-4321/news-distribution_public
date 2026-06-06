import unittest

from src.ranker import RankedStory
from src.summarizer import _evidence_level, _usable_evidence


def _story(summary_seed: str) -> RankedStory:
    return RankedStory(
        title="Nvidia launches a new AI chip",
        url="https://example.com/story",
        source="Reuters",
        published_at="2026-06-06T00:00:00+00:00",
        importance_score=9,
        reason="重要芯片发布",
        summary_seed=summary_seed,
    )


class SummaryEvidenceTests(unittest.TestCase):
    def test_title_and_source_are_not_treated_as_extra_evidence(self) -> None:
        story = _story("Nvidia launches a new AI chip Reuters")

        self.assertEqual(_usable_evidence(story), "")
        self.assertEqual(_evidence_level(story), "headline_only")

    def test_real_snippet_is_preserved(self) -> None:
        story = _story("The company said shipments will begin next quarter.")

        self.assertEqual(
            _usable_evidence(story),
            "The company said shipments will begin next quarter.",
        )
        self.assertEqual(_evidence_level(story), "snippet")


if __name__ == "__main__":
    unittest.main()
