---
name: google-ads-review
description: Review an existing Google Ads account and prepare bounded, evidence-backed recommendations.
metadata:
  category: managed
---

# Google Ads Review

Adapted from the MIT-licensed [Graphed Google Ads plugin](https://github.com/graphed-inc/marketing-skills/tree/main/plugins/google-ads). The original Mastra agent, Graphed warehouse, DataForSEO tool, dashboard, and daily job are not installed by this skill.

Require an existing account or supplied export, date range, campaign scope, business goal, and task-provided durable output location. A granted Metricool MCP connection can provide Google Ads account, campaign, ad-group, ad, and performance evidence when that account is connected and those tools expose the needed fields. Inspect the live tool catalog and read-only schemas before using it; Metricool's ability to manage ads is not permission to mutate them. An attached Google Ads connector or supplied export is another valid source. If none is available, return `needs_input`. OpenSEO can add keyword, CPC, SERP, and organic-search context, but it is not Google Ads spend or conversion data. A Serper result is discovery evidence, not account performance. Do not guess customer IDs, campaign IDs, spend, conversions, or keyword volume.

Collect campaign, ad group, search-term, keyword, cost, conversion, and attribution data only through authorized read-only tools. Preserve units, currency, reporting timezone, account scope, filters, dates, and provider request IDs. Compute rates from their denominators; distinguish zero conversions from missing conversion data. Use the Stimulir model gateway to synthesize findings, not to fabricate metrics.

Prepare a reviewable Testing → Winners proposal: terms to investigate, negatives to inspect, budget changes with estimated impact and uncertainty, and evidence for each. New keyword research may use granted OpenSEO tools or supplied evidence; inspect pricing before paid calls. Use the harness browser for landing-page inspection, or the configured browser-use path in a sandbox when native browsing is unavailable. Browser observations do not substitute for Ads metrics. No Ads mutation is implicit in this skill. For requested writes, require an attached write-capable connector, exact campaign/target, explicit user authorization for spend changes, a preflight preview, and idempotency or change IDs. Never emulate Ads writes with browser or shell credentials. Do not create a recurring schedule unless requested.

Persist the source snapshots and a recommendation artifact; return `complete`, `partial`, `needs_input`, or `blocked` with the exact stages completed. Never label recommendations as applied changes.
