---
name: competitor-ad-research
description: Analyse competitor ad creative, messaging and offers with traceable public evidence.
metadata:
  category: managed
---

# Competitor Ad Research

Collect public ad IDs/URLs, advertiser, placement, first/last observed date, hook, offer and landing page. Deduplicate repeated ad IDs and creative variants before comparing themes. Longevity, repeated variants and engagement are proxy signals, never verified ROAS or conversion rate. Transcripts and keyframes must refer to actual collected media; do not claim a media-analysis capability from catalog presence alone. No campaign launch, publishing, audience upload or spend change is part of this skill.

## Managed execution

This package uses attached connector tools or environment-bound helper credentials and no human CLI session. It is usable alone with supplied evidence or an attached AdRadar connector. For the full six-stage deployment, explicitly select `audience-research` plus all six stage skills; selecting this skill never imports siblings automatically. Use the coordinator's bounded Treg helper only when that package is installed and deployment policy authorizes the endpoint and spend. Read raw provider responses before normalizing: HTTP success does not prove provider success. No direct OpenSEO API integration is implied.

## AdRadar collection

When the deployed agent exposes `adradar_collect`, use that typed tool for public Meta Ad Library collection. Read its actual input schema. Supply the numeric advertiser `page_id` from the user's brief or a verified source, a two-letter country code or `ALL`, and optionally `max_scrolls` (1–20, default 3). Do not guess a page ID from a company name or substitute an arbitrary URL. This connector does not require a public-scraper API key, a human CLI login or a Treg token. No notification or campaign tools are part of this collection.

The runtime owns the pinned CLI, browser dependencies, sandbox execution and client/agent grants. Do not download or invoke another CLI, inject credentials, or bypass a missing connector with raw shell commands. If the connector is unavailable, use supplied evidence or report the missing input; use another authorized source only if the task permits it. Supplied-evidence-only mode must not invoke AdRadar.

Inspect the tool's `complete|no_data|blocked` status and actual returned records. Preserve collection time, advertiser/country, ad IDs, real ad/landing URLs, durable artifact/snapshot URIs when returned, and provenance including CLI/adapter/browser versions, bundle hash and request arguments. `artifact_path` and `snapshot_path` are local sandbox paths, not durable references; persist their files in the final artifact bundle when durable host URIs are unavailable. Missing dates or URLs remain unknown. Local `first_seen`/`last_seen` observations are distinct from an ad's publisher-reported start date: a first collection does not establish continuous activity before that observation. A bounded collection is not a complete inventory. Treat an upstream "winner" label as a longevity heuristic, never profitability or measured performance.

Normalize only retrieved ad observations into evidence rows. An ad ID alone does not establish its hook, offer or audience; quote or describe only the creative actually returned, label audience/theme interpretation as inferred and cite its evidence IDs. A connector `complete` response means collection succeeded; the research stage is complete only after supported evidence and claims are validated. `no_data` is reserved for an explicitly successful empty collection; denied grants, unavailable binaries, timeouts, challenges and parser/provider failures are `blocked`. Preserve partial evidence if returned with a blockage and explain its limited coverage. Persist raw connector artifacts before committing the normalized stage. Read the [AdRadar provenance reference](references/adradar.md) when normalizing connector results.

## Artifact contract

Write one JSON object with `schema_version: 1`, `stage: competitor-ad-research`, `status: complete|no_data|blocked`, `evidence: []`, and `claims: []`. Each evidence row has `id`, `text`, `kind: observed|inferred|synthetic`, `source_url` (HTTP(S), no credentials), and timezone-aware `retrieved_at`. Each claim has `text`, `kind` and nonempty `evidence_ids`. Claims must reference evidence in this artifact. Use unique stable IDs; preserve imported IDs verbatim. An observed claim requires observed evidence; synthetic sources require synthetic claims. Cite only actually retrieved material. Evidence validation cannot prove a quote is truthful; compare it to its raw source.

`complete` requires nonempty evidence and claims. Use `no_data` only for a completed search with no evidence, with empty arrays and a `reason`. Missing authorization, secrets, inputs or provider failure is `blocked` with a `reason`; it must not look like a successful empty search. Never fabricate a plausible report to fill missing data.

Validate with `python3 helpers/evidence.py /absolute/path/stage.json` from this package directory. The helper is standalone and uses only the standard library. Write output only to the task-provided artifact path. Sandbox files are not durable by themselves: hand them to the runtime's artifact persistence mechanism before ending the attempt. The coordinator commits validated stage artifacts and exports the final result.
