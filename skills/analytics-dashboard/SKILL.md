---
name: analytics-dashboard
description: Design and build an evidence-backed analytics dashboard from an inspected data source and approved read-only query access.
metadata:
  category: managed
---

# Analytics Dashboard

Adapted from the MIT-licensed [Graphed analytics-dashboard skill](https://github.com/graphed-inc/marketing-skills/tree/main/skills/analytics-dashboard) for a Stimulir managed sandbox. Build a dashboard only for an actual destination supplied by the task. The Graphed CLI, warehouse, SDK, and templates are not Stimulir runtime tools; do not call or import them.

## Inputs

Require a business question or metric, destination repository or artifact format, and one of:

- a supplied schema and bounded rows/export; or
- an attached, authorized read-only data tool whose catalog and query contract you can inspect.

Metricool MCP is a suitable source for connected social, website, and ad-account reporting when its granted tools expose the requested metric and dimensions. OpenSEO can supply SEO, Search Console, and connected Analytics evidence for a search-focused dashboard. Inspect the actual project/brand, account connections, tool schema, reporting period, and freshness before choosing either source. A source's dashboard UI is not proof that the managed harness can query it.

Check the selected project and tenant scope before querying. Never infer a schema from a connector name. If source or metric is ambiguous, list the real available choices and ask once. If no schema or data access is available, return `blocked` with the exact missing input; do not invent dashboard values.

## Workflow

1. Inspect the destination's existing app, chart library, styles, tests, and data access conventions before editing. Use the harness's native browser for a rendered UI when available, or a configured browser-use path in a sandbox without native browsing. Browser access helps inspect the interface; metrics still come from a granted data tool or export. Do not copy a Graphed or Next.js template into an unrelated app.
2. Inspect source tables, column names, types, units, date timezone, freshness, and row-level permissions. Use only permitted read-only queries. Bound row count and date range. Do not write SQL until schema is known; parameterize user values using the actual data tool contract.
3. Select one primary metric and define its numerator, denominator, aggregation, source columns, and filter. Treat counts and sums differently. Label unavailable comparison periods or missing dates rather than filling them with fabricated zeros.
4. Build the smallest dashboard that answers the question. For a dated source, include a changeable date range and at least two useful views of the metric. For a source without dates, use a breakdown and state that a time series is unavailable. Show source and freshness beside the result. Follow the destination's existing component and theme rules.
5. Verify totals against a direct aggregate query or supplied fixture. Exercise empty, loading, error, and unauthorized states. Check that changing the date range changes the query and displayed data.

## Managed execution and output

Use only attached host tools or explicitly selected Vault bindings. A human CLI login and `@graphed-inc/sdk` are not available in the Stimulir sandbox. Do not install a provider CLI or bypass connector grants. Store any generated code, query definitions, and a short provenance manifest in the task-provided durable artifact location. Sandbox paths alone are not durable.

Return `complete`, `needs_input`, or `blocked`; include the source identifier, exact table/columns, metric definition, date bounds, timezone, freshness, query/tool identifiers, and verification result. Never claim a live dashboard was deployed when only an artifact or draft was produced. Do not deploy or publish without the task's authorization.
