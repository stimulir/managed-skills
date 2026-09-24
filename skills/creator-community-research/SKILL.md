---
name: creator-community-research
description: Map creators and communities relevant to a proposed buyer and their recurring questions.
metadata:
  category: managed
---

# Creator Community Research

Find relevant public creators and communities through both niche/topic relevance and audience evidence. Summarize recurring questions with citation URLs and preserve platform, observation date and available engagement denominators. Followers and likes are attention signals, not proof of purchasing authority. Avoid inferring sensitive traits or harvesting personal contact details. Explain why a creator reaches the proposed buyer instead of merely discussing AI. No outreach or posting is included.

## Managed execution

This package uses environment-bound credentials and no human CLI session. It is usable alone with supplied evidence. For live collection in the six-stage deployment, explicitly select `audience-research` plus all six stage skills; selecting this skill never imports siblings automatically. Use the coordinator's bounded Treg helper only when that package is installed and deployment policy authorizes the endpoint and spend. Read raw provider responses before normalizing: HTTP success does not prove provider success. No direct OpenSEO API integration is implied.

## Artifact contract

Write one JSON object with `schema_version: 1`, `stage: creator-community-research`, `status: complete|no_data|blocked`, `evidence: []`, and `claims: []`. Each evidence row has `id`, `text`, `kind: observed|inferred|synthetic`, `source_url` (HTTP(S), no credentials), and timezone-aware `retrieved_at`. Each claim has `text`, `kind` and nonempty `evidence_ids`. Claims must reference evidence in this artifact. Use unique stable IDs; preserve imported IDs verbatim. An observed claim requires observed evidence; synthetic sources require synthetic claims. Cite only actually retrieved material. Evidence validation cannot prove a quote is truthful; compare it to its raw source.

`complete` requires nonempty evidence and claims. Use `no_data` only for a completed search with no evidence, with empty arrays and a `reason`. Missing authorization, secrets, inputs or provider failure is `blocked` with a `reason`; it must not look like a successful empty search. Never fabricate a plausible report to fill missing data.

Validate with `python3 helpers/evidence.py /absolute/path/stage.json` from this package directory. The helper is standalone and uses only the standard library. Write output only to the task-provided artifact path. Sandbox files are not durable by themselves: hand them to the runtime's artifact persistence mechanism before ending the attempt. The coordinator commits validated stage artifacts and exports the final result.
