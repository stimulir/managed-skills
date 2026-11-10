---
name: enrich-linkedin-engagers
description: Collect visible LinkedIn post commenters and reactors with an authorized browser or normalize a supplied export, then optionally enrich and verify contacts with traceable run artifacts.
metadata:
  category: managed
---

# LinkedIn Engager Enrichment

Adapted from the MIT-licensed [Graphed enrichment skill](https://github.com/graphed-inc/marketing-skills/tree/main/skills/enrich-linkedin-engagers) for Stimulir managed execution. Its Graphed CLI, Apify actors, Apollo tools, MillionVerifier tools, database, and cron templates are not assumed to exist here. Do not invoke their names as though Stimulir provides them.

## Inputs and capability check

Require one LinkedIn profile or post URL, or a supplied engagement export. For live collection, use the harness's authorized browser capability when available; Codex's native browsing can serve this role. In a sandbox without native browsing, a configured browser-use agent may serve if it can open the comments/reactions panels and paginate them. The `web-scrape` helper only extracts page text and is insufficient by itself for an engager list. A browser session may inspect only content the authorized account can normally view. If the harness has a dedicated collector, inspect its grants and schema before using it. Before email matching, CRM exclusion, or verification, separately confirm the task requests those stages and inspect the actual granted tool schemas, pricing, and limits. Keep collection, matching, exclusion, and verification as distinct stages. A URL by itself does not authorize paid enrichment or outreach.

For a profile URL, identify the requested recent posts first; for a post URL, inspect that post. Open the comments and reactions panels, paginate or scroll within a stated limit, and capture each visible person with the source post URL and engagement type. Record the visible count, number of pages inspected, and whether loading stopped because of a limit, unavailable content, or an access challenge. Do not use scraped cookies, bypass access controls, or infer unseen engagers from aggregate counts. If no authorized browser or granted collector is available, process a supplied export or return `needs_input`. Search snippets are discovery evidence, not an observed engager list. Do not schedule recurring collection unless requested.

## Run procedure

1. Record input URL/export identity, retrieval time, source permission, run ID, and tenant/project scope. Bound posts, pages, and people using the browser plan or granted tool contract. Preserve source URLs and bounded browser observations or collector receipts through the task's durable artifact mechanism.
2. Normalize each observed person to `linkedin_url`, `full_name`, `title`, `engagement_type`, `comment_text`, and `source_post_url`, retaining which fields were actually returned. Deduplicate by canonical profile URL; retain a comment over a reaction for the same person. Keep incomplete and URN-only profiles as explicit skips.
3. Report counts before any paid match: observed engagements, unique profiles, skipped profiles, and the tool's current cost estimate if available. Apply an explicit run limit. If the limit or authorization is missing, stop before paid calls with `needs_input`.
4. Match emails only through an attached, granted enrichment tool. Record each lookup's provider, request ID, match status, and evidence. Do not guess addresses or treat a person's name as proof of an email. If CRM exclusion was requested, inspect the actual CRM data contract and exclude matches before verification.
5. Verify remaining addresses only through an attached, granted verifier. Preserve its raw status; do not rename `unknown` as deliverable. Keep `not_found`, `excluded`, `invalid`, and `unknown` rows in the run record. Do not email, upload audiences, or publish contact lists as a side effect.

## Output

Persist a run manifest and a bounded CSV or JSON artifact with per-row provenance, stage status, skips, costs or credit estimates, and pending provider request IDs. A sandbox folder alone is ephemeral. Resume an outstanding provider job by request ID instead of starting an identical paid job. Redact credentials and do not place raw provider tokens in artifacts.

Return `complete`, `partial`, `needs_input`, or `blocked`, with counts for each stage. `complete` describes only the stages actually requested and performed. If the browser exposed only part of the engagement list, mark collection partial and report its bounds. If only supplied engagement data was normalized, say so; never imply live LinkedIn collection, Apollo matching, email verification, CRM exclusion, or deliverability testing occurred.
