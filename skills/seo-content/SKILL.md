---
name: seo-content
description: Research search demand, draft sourced SEO content, and prepare a reviewable publishing plan using Stimulir models.
metadata:
  category: managed
---

# SEO Content

Adapted from the MIT-licensed [Graphed SEO plugin](https://github.com/graphed-inc/marketing-skills/tree/main/plugins/seo). This is a Stimulir managed workflow, not the Graphed Next.js application, warehouse, cron, or CMS integration.

## Inputs and research

Require product/site, target audience, market/language, content goal, and a task-provided durable output location. Inspect the live site and existing content before planning. Use the attached OpenSEO connector as the primary source for keyword, SERP, domain, rank-tracker, and connected Search Console evidence when it is granted. Discover its actual tools with `openseo_tools` before calling `openseo_call`, and use the selected OpenSEO project; the host injects that provider project. A connected Google Analytics property may add first-party site evidence when the granted tools expose it. Do not assume a connection or metric exists merely because OpenSEO is attached.

For page inspection, use the harness's native browser when available. In a sandbox without that browser, use the selected `web-scrape` or `deep-research` browser-use path only when its optional browser dependencies, Chromium, and model connection are configured; otherwise use the HTTP fetch path and report pages it cannot render. Serper through the selected `deep-research` package can supplement source discovery when `SERPER_API_KEY` is bound. `search-demand` and `audience-research` can provide additional evidence when selected. None of these packages is imported automatically.

Record exact keyword/source URLs, retrieval times, geography, volume units, competition metrics, and limitations. Separate observed metrics from model judgment. Avoid claiming that a draft will rank. Choose a small queue of topics with distinct intent and check for overlap with existing pages.

## Draft and review

Use the deployed Stimulir model gateway for outlining and drafting. Do not require an OpenRouter, OpenAI, or Graphed model key. Ground factual claims in inspected primary or credible sources and retain citations. Draft title, slug, target query, intent, outline, article Markdown, meta description, internal link suggestions, and claim/source map. Check originality, unsupported claims, working links, and brand voice. Keep drafts in durable task artifacts with a manifest and review status.

Publishing and refresh are separate actions. If an attached CMS tool with the requested destination and write grant exists, inspect its schema and create a draft only when authorized. Publishing a live article, changing a live page, scheduling a recurring job, or sending promotional messages needs the user's explicit request and a reviewed final draft. Use provider IDs to avoid duplicate creation or updates. Report `needs_input` when the CMS or destination is missing; do not install Graphed templates or invent endpoints.
