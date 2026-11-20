# Treg collection contract

## Discovery and access

Use attached `catalog_search` then `catalog_get` (or an installed CLI's `treg catalog search` / `treg catalog get`) to discover actual endpoint IDs, methods, input requirements, response shape, price and freshness controls. Inspect registered team tools when relevant. Confirm organization scope without printing credentials. Catalog discovery is not evidence that a provider call succeeded.

Managed execution must use a selected `TREG_TOKEN` Vault binding through a reviewed adapter, or attached granted Treg tools. Never install a login flow or read a human credential file in the sandbox. The separately installed `audience-research` collection helper can be reused only when explicitly included with its run/policy contract: it supports allowlisted read-only GET endpoints, reserves costs and deduplicates successful queries within a run. It is not bundled here. POST-only endpoints require a compatible reviewed read-only adapter; do not change methods or call arbitrary URLs to evade a policy. Do not require all six research stages merely to collect trend data.

## Scope, price and retrieval

Inspect applicable per-call, per-result and overflow prices before spending; communicate the bounded expected cost. Honor the existing task/deployment budget and endpoint allowlist. No policy means no implied paid-call allowance. Catalog reads and local planning can proceed while required collection authorization is missing. Do not alter the budget or register new secrets/tools as part of trend research.

Choose compatible inputs first, then observed reliability, price and freshness. Bound query results and pagination; stop at the task limits. Save endpoint ID, sanitized request, call/receipt ID, actual reported cost and raw response. Verify provider-level errors, response arrays, units and record identity even when HTTP succeeds. Preserve only safe provenance headers, never tokens or authorization headers.

Retain provider observation/retrieval time and Treg cache fields (`X-Treg-Cache`, `X-Treg-Fetched-At`, `X-Treg-Age`) when exposed, separately from the local receipt time. Use documented max-age controls when the workflow needs fresher data; forcing a live call can change cost. A cached response can support content discovery while being unsuitable for a new momentum observation.

## Retry versus refresh

A timed-out call with uncertain outcome requires reconciliation; if the supported interface offers idempotency, retry the identical request with the same key. An intentional later tracking refresh is new work and needs a new key/run, otherwise it can replay old data. The audience helper intentionally reuses successful queries within a run; use a new authorized run for refresh and carry forward normalized history separately.

Do not automatically retry reservations left uncertain by the helper. Correct parameter/auth/policy errors before any further call. After a confirmed transient failure, at most one compatible alternative may be attempted within the same authorized scope and remaining budget; state the provider change and do not compare incompatible metric definitions across providers. Preserve unresolved calls as gaps, not zero engagement.

No external call is needed when the task is solely to define the workflow or analyze supplied exports. Missing live tools should not prevent useful local skill or campaign work.
