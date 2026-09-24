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
