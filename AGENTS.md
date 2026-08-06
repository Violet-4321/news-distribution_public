# Daily News Brief Project

This project is a high-signal news briefing system.

The goal is not to maximize news coverage.

The goal is to identify and summarize only the most important developments from the previous 24 hours.

## Selection Philosophy

Prefer omission over inclusion.

A briefing with 5 important stories is better than a briefing with 10 average stories.

Never add filler content.

## News Priorities

The briefing covers two core areas as parallel priorities. A story only needs to be important in one of them, not both:

* Business and economics: markets, company earnings, trade, macro, monetary policy
* AI: model releases, AI chips and infrastructure, AI companies and industry trends

Also prioritize:

* Global coverage, with emphasis on China and other major powers (United States, Europe, Japan, India)
* Major company events in China and worldwide
* Major macroeconomic events
* Balanced coverage across the two core areas

## Exclusions

Generally exclude:

* minor feature updates
* technical changelogs
* routine company announcements
* entertainment news
* sports news
* celebrity news

Unless the event is exceptionally important.

## Output Goals

Between 5 and 10 stories per day (default 10, configurable via `MAX_STORIES`).

All summaries should be written in Chinese.

The entire briefing should be readable in under 5 minutes.

Every briefing should include the VIX index and a brief interpretation.
