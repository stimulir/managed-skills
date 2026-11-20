# Trend evidence

Keep external trend evidence separate from owned content results. A bounded watchlist should record platform, account/topic, audience relevance and collection source. Use Treg discovery and retrieval as described in [Treg collection](treg-collection.md). Owned Metricool results may inform selection but are a separate evidence source; do not assume a platform-wide trend feed.

For each tracked post, retain its stable platform ID/URL, creator, publication date when available, format, hook/topic, observed metrics, metric definitions, retrieval timestamp and raw evidence reference. Record audience size and paid/organic status only when available; unknown is not organic. Append snapshots rather than overwriting history; deduplicate reposts where identifiable.

With two comparable snapshots, calculate growth as metric delta divided by elapsed hours. Record the interval and flag negative corrections or changed metric definitions instead of calling them declining engagement. Acceleration requires multiple intervals. One snapshot supports “high observed engagement,” not a measured rising trend. Compare posts within platform, format and similar age; use a creator's recent comparable-post median only if actually collected, with sample size. Do not invent saves, retention, revenue or hidden metrics.

Cluster recurring hooks, formats and buyer questions across independent accounts. A single hit is a candidate signal, not evidence of widespread adoption. Rank candidates with an explicit rationale covering recent growth, freshness, repeated observations and relevance to the product's buyer/task. Keep missing evidence visible instead of disguising it in a precise score. Age out stale candidates on a stated campaign-specific window.

Each daily shortlist includes the source post, what is performing, why it may transfer, the original product proof to create, and a use/watch/reject decision. Borrow a structure or audience insight, not another creator's footage, identity or testimonial without rights. Link adopted trends to local creative IDs, then evaluate those adaptations against owned engagement and business outcomes.

## Report contract

Write one JSON object with `schema_version: 1`, `stage: content-trend-research`, `status: complete|partial|no_data|blocked`, `goal_id`, `campaign_id`, `run_id`, timezone-aware `retrieved_at`, `scope`, `watchlist`, `snapshots`, `opportunities`, `gaps`, `evidence`, and `claims`. Collections may be empty with a reason; partial results name failed or uncollected scope. Include safe durable artifact references for raw receipts and prior state.

Each evidence row has a unique `id`, `text`, `kind: observed|inferred`, source URL and retrieval time with its basis. Each claim has `text`, `kind` and nonempty `evidence_ids` resolving to this report. Observed claims require observed evidence. Preserve imported evidence IDs unchanged; scope new IDs to the source/run to avoid collisions.

Each snapshot records `snapshot_id`, stable `post_id`/URL, platform, provider/endpoint, publication time when known, receipt time, provider observation time when known, cache metadata when exposed, metrics with names/units/definitions, and evidence IDs. Use null for unknown values. Preserve prior observations and their original timestamps. If actual observation freshness is unknown, do not compute definitive interval velocity from receipt timestamps alone; label it unknown or a clearly caveated estimate.

Each opportunity records `opportunity_id`, source post IDs and evidence IDs, audience/task fit, pattern, original hook proposal, required product proof, CTA intent, hypothesis, `decision: use|watch|reject` and rationale. Growth calculations cite snapshot IDs, elapsed interval and comparable metric definitions; source popularity is never labeled observed sales performance. The consuming production workflow adds creative IDs and later owned-result references without rewriting source evidence.

Before delivery, check unique IDs, resolving references, timestamp ordering, source/metric comparability, numeric calculations, missing-data labels, and raw-to-normalized fidelity. These checks are agent responsibilities; this package does not ship an executable schema validator. Do not claim validator success from merely parsing JSON.
