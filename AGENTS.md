# Daily News Brief Project

This project is a high-signal news briefing system.

The goal is not to maximize news coverage.

The goal is to identify and summarize only the most important developments from the previous 24 hours.

## Selection Philosophy

Prefer omission over inclusion.

A briefing with 5 important stories is better than a briefing with 10 average stories.

Never add filler content.

## News Priorities

The briefing covers three core areas as parallel priorities with a strict macro-over-micro bias. A story only needs to be important in one of them, not both:

* Macro business and economics: monetary policy and central banks, interest rates, inflation, GDP and growth, fiscal policy, trade policy and tariffs, systemic capital-market moves, economy-wide trends
* Macro AI: national AI strategy and regulation, frontier model generations, AI capex and data-center buildouts, compute and chip supply-chain dynamics, AI's economic and policy implications
* Major international politics, military, and security: armed conflicts, major-power diplomacy and summits, elections and regime changes with global consequences, sanctions and treaties, military deployments and defense policy, national-security moves that reshape international relations

Demote micro news (a single company's earnings, routine product releases, individual stock moves, niche technical updates, routine domestic politics) unless the event is systemically significant and moves markets, industries, or international relations.

Also prioritize:

* Global coverage, with emphasis on China and other major powers (United States, Europe, Russia, Japan, India) and major regional flashpoints
* Balanced coverage across the three core areas

## Exclusions

Generally exclude:

* minor feature updates
* technical changelogs
* routine company announcements
* single-company earnings that are not market-moving
* routine product and feature releases
* entertainment news
* sports news
* celebrity news
* local political trivia

Unless the event is exceptionally important.

## Output Goals

Between 5 and 10 stories per day (default 10, configurable via `MAX_STORIES`).

All summaries should be written in Chinese.

The entire briefing should be readable in under 5 minutes.

Every briefing should include the VIX index and a brief interpretation.
