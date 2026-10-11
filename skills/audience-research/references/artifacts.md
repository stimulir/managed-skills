# Stage artifact examples

A deliberately fictional shape example; never use these values as research evidence:

```json
{
  "schema_version": 1,
  "stage": "vendor-research",
  "status": "complete",
  "evidence": [{"id":"vendor:example:1","text":"Exact verified source observation","kind":"observed","source_url":"https://example.com/case-study","retrieved_at":"2026-09-24T12:00:00+00:00"}],
  "claims": [{"text":"Supported conclusion","kind":"inferred","evidence_ids":["vendor:example:1"]}]
}
```

For `avatar-synthesis`, include `avatars`, each with `id`, `buyer`, `trigger`, `pain`, `offer`, nonempty `channels`, and nonempty `claims` using the same citation contract. Copy supporting evidence rows exactly from committed collection artifacts.

For `experiment-feedback`, include nonempty `experiments`: `experiment_id`, `avatar_id`, `creative_id`, `metric`, `window_start`, `window_end`, numeric `numerator` and `denominator`, and `evidence_id`. Rate denominators must be positive, numerator between zero and denominator, and the citation must be observed owned data with `ownership: "owned"` on its evidence row. Window boundaries must both be ISO calendar dates or both timezone-aware ISO timestamps, ordered start before end (same calendar date allowed). An ownership label requires actual owned account/report provenance; structural validation cannot establish ownership itself. Additional source/account and attribution metadata should be preserved. A collector cannot infer ownership from public ad statistics.

Missing account data:

```json
{"schema_version":1,"stage":"experiment-feedback","status":"blocked","reason":"Owned campaign outcomes and experiment-to-creative mapping are not supplied","evidence":[],"claims":[]}
```

Each output stage summary has `stage`, `status`, `artifact_path`. Paths are relative to the run directory; publish the bundle using the runtime's task-artifact mechanism. They are not public URLs.

Treg protocol reference verified 2026-09-24: https://treg.to/llms.txt. Endpoint price/access is GET `/catalog/endpoints/<id>/access`; collection is GET `/call/<id>`; env token maps to `X-Treg-Token`; `X-Treg-Route-Max-Cost` caps the request in USD. `X-Treg-Cost-Micro` is the actual charge receipt. Request bodies and write operations are outside this helper's scope.

## Connector provenance

A fictional OpenSEO shape example; none of these values is a finding. A real
artifact must copy the actual returned row URL, market, collection time and
request arguments. Extra provenance fields are retained by validation and
checkpoint/export. The raw artifact path is a persisted bundle reference, not
a public URL. Do not put credentials in any field.

```json
{
  "schema_version": 1,
  "stage": "search-demand",
  "status": "complete",
  "evidence": [{
    "id": "search:example:1",
    "text": "OpenSEO returned example.com/product as an organic result for the supplied query. This is a search-result observation, not a buyer outcome.",
    "kind": "observed",
    "source_url": "https://example.com/product",
    "retrieved_at": "2026-10-11T05:00:00+00:00",
    "provenance": {
      "provider": "openseo",
      "tool": "get_serp_results",
      "provider_project_id": "example-provider-project",
      "query": "example buyer problem",
      "country": "United Kingdom",
      "language": "English",
      "request_arguments": {"keywords": ["example buyer problem"]},
      "raw_artifact_path": "raw/openseo-serp-example.json"
    }
  }],
  "claims": [{
    "text": "This domain is a candidate for comparable-vendor research; its buyers and product fit still need verification.",
    "kind": "inferred",
    "evidence_ids": ["search:example:1"]
  }]
}
```

Tool parameters vary; use the live granted schema instead of copying this
example's request arguments. Record metric units, observation period and cache
age when returned. Missing units, dates or metrics stay unknown. If no real
citation URL is returned or supplied, retain the raw result as a task artifact
and explain the citation gap rather than inventing an evidence row.

A `get_project_context` response supports statements such as “the saved project
profile lists these competitors”; it does not independently establish those
vendors' customers, success or fit. Keep connection-check context in generic
`artifacts` instead of marking a collection stage complete. A provider error or
missing grant is `blocked`, not `no_data`. Copy complete evidence rows, including
provenance, unchanged into avatar synthesis.
