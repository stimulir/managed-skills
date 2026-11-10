# Marketing skill routing

## Plan

- [x] Inspect the five new managed skills and existing browser-use/OpenSEO contracts.
- [x] Define browser routing for Codex and sandbox runs.
- [x] Update SEO, Google Ads, analytics, outbound, and engager instructions.
- [x] Update catalog wording and verify routing and metadata.

## Review

All five skill packages retain `metadata.category: managed`. Console's real `parse_frontmatter`, `skill_category`, and `parse_pip_deps` functions accept each local package with no parse warning. Each has a valid `pyproject.toml`, agent metadata, and an upstream MIT notice. Focused routing checks passed. Codex uses its native browser; a sandbox can use browser-use when configured. The existing `web-scrape` helper extracts page text and does not by itself navigate LinkedIn engagement panels. OpenSEO is the SEO source; Metricool is an optional granted Ads/analytics source; Apollo and Gmail are optional granted reply tools. `test_audience_research.py` passed 28 tests and `test_research_report_provenance.py` passed 7 tests when run directly. Broad unittest discovery stalled at import and was interrupted. No live connector account, browser session, paid tool call, or workspace import was tested. The local branch is behind GitHub `main`; integration must retain current main's changes.
