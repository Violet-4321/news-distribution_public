import unittest
from datetime import timezone

from src.news_collector import (
    _clean_text,
    _is_major_bls_release,
    _is_major_fed_release,
    _parse_feed_datetime,
)


class OfficialReleaseFilterTests(unittest.TestCase):
    def test_google_rss_html_is_reduced_to_readable_text(self) -> None:
        value = (
            '<a href="https://news.google.com/example">Nvidia launches a chip</a>'
            '&nbsp;&nbsp;<font color="#6f6f6f">Reuters</font>'
        )

        self.assertEqual(_clean_text(value), "Nvidia launches a chip Reuters")

    def test_fed_keeps_policy_statements_but_not_minutes(self) -> None:
        self.assertTrue(_is_major_fed_release("Federal Reserve issues FOMC statement"))
        self.assertFalse(
            _is_major_fed_release(
                "Minutes of the Federal Open Market Committee, April 28-29, 2026"
            )
        )

    def test_employment_requires_large_change_or_deterioration(self) -> None:
        self.assertFalse(
            _is_major_bls_release(
                "Employment Situation",
                "Payroll employment increases by 172,000 in May",
            )
        )
        self.assertTrue(
            _is_major_bls_release(
                "Employment Situation",
                "Payroll employment increases by 250,000 in May",
            )
        )
        self.assertTrue(
            _is_major_bls_release(
                "Employment Situation",
                "Payroll employment decreases by 50,000 in May",
            )
        )

    def test_price_releases_use_separate_thresholds(self) -> None:
        self.assertFalse(
            _is_major_bls_release(
                "Consumer Price Index",
                "CPI for all items rises 0.2% in May",
            )
        )
        self.assertTrue(
            _is_major_bls_release(
                "Consumer Price Index",
                "CPI for all items rises 0.4% in May",
            )
        )
        self.assertFalse(
            _is_major_bls_release(
                "Producer Price Index",
                "PPI for final demand advances 0.4% in May",
            )
        )
        self.assertTrue(
            _is_major_bls_release(
                "Producer Price Index",
                "PPI for final demand falls 0.1% in May",
            )
        )

    def test_feed_datetime_accepts_bls_iso_format(self) -> None:
        parsed = _parse_feed_datetime("2026-05-12T08:30:00Z")

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.isoformat(), "2026-05-12T08:30:00+00:00")


if __name__ == "__main__":
    unittest.main()
