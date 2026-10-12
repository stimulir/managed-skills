# AdRadar result provenance

The connector returns `status`, optional `reason`, `ads`, `retrieved_at`,
`source_url` and `provenance`. `artifact_path` points to the normalized result
inside the sandbox; `snapshot_path` points to its raw snapshot when available.
Neither local path is durable by itself. Successful host persistence supplies
tenant-scoped `artifact_uri` and `snapshot_uri`; preserve these durable references
when returned. Inspect the returned `ads` shape;
do not assume every creative contains text, media, dates or a landing page.
An empty scrape without an explicit successful-empty marker is `blocked`, not
`no_data`. The snapshot artifact is raw collection data, not a completed stage.

This fictional normalization example is not research evidence. A real artifact
copies actual returned identifiers, values and provenance. Use an ad's real URL
when returned; a real returned collection URL can support an observation from
that collection when explicitly identified as such. Never invent ad/media URLs.

```json
{
  "schema_version": 1,
  "stage": "competitor-ad-research",
  "status": "complete",
  "evidence": [{
    "id": "adradar:example-ad:creative",
    "text": "The collected creative contains the text: Example supplied creative quote.",
    "kind": "observed",
    "source_url": "https://www.facebook.com/ads/library/?id=123456789",
    "retrieved_at": "2026-10-11T12:00:00+00:00",
    "provenance": {
      "provider": "adradar",
      "tool": "adradar_collect",
      "cli_revision": "607341149061e7ac159407dabe01c9fa3c14ee61",
      "adapter_version": "1",
      "playwright_version": "1.61.0",
      "bundle_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "page_id": "987654321",
      "country": "GB",
      "ad_id": "123456789",
      "request_arguments": {"page_id": "987654321", "country": "GB", "max_scrolls": 3},
      "artifact_uri": "/api/v1/compute/agents/connector-artifacts/00000000-0000-4000-8000-000000000001",
      "snapshot_uri": "/api/v1/compute/agents/connector-artifacts/00000000-0000-4000-8000-000000000001?raw=true"
    }
  }],
  "claims": [{
    "text": "The creative may address this buyer pain; audience fit and performance still require validation.",
    "kind": "inferred",
    "evidence_ids": ["adradar:example-ad:creative"]
  }]
}
```

Copy returned revision, adapter version, browser version, bundle hash and request
arguments instead of assuming the example values. Prefer actual durable URIs
provided by the host; they require tenant-scoped access and are not public source
citation URLs. If only local paths exist, copy those files into the task's final
artifact bundle and persist that bundle before ending the attempt. Then record
the actual persisted bundle path/reference. Never label a sandbox path durable
or invent a successful persistence URI. Missing raw snapshots remain missing.
Keep `first_seen`, `last_seen` and publisher start dates separately when present,
with their original precision and meaning. Do not replace missing ad dates with
the retrieval timestamp. A single bounded collection cannot establish ad
longevity, impressions, targeting, conversions or ROAS. Copy complete evidence
rows unchanged when incorporating them into avatar synthesis.
