# Stimulir Managed Skills

Sandbox-managed AI capabilities for Stimulir workspaces. These skills run in
the Stimulir code-runtime sandbox, receive the active workspace environment,
and produce durable task artifacts. They do not depend on a human CLI login.

For adopter-repository onboarding, trace capture, prompt evaluation, RSI, and
promotion workflows, use the separate
[`stimulir/skills`](https://github.com/stimulir/skills) operator catalog.

## Catalog

| Skill | Purpose | External key |
|---|---|---|
| [`web-scrape`](./skills/web-scrape/) | Extract clean text from URLs or followed links in parallel. | None |
| [`deep-research`](./skills/deep-research/) | Discover, fetch, and synthesize an evidence-backed report and CSV. | `SERPER_API_KEY` |
| [`opposition-enrich`](./skills/opposition-enrich/) | Build a sourced competitor or opposition brief. | `SERPER_API_KEY` |
| [`scenario-simulate`](./skills/scenario-simulate/) | Simulate reactions from a described synthetic population. | None beyond the Stimulir gateway key |
| [`audience-research`](./skills/audience-research/) | Coordinate six evidence-backed audience research stages with budgeted collection and checkpoints. | `TREG_TOKEN` for Treg; attached OpenSEO connector optional |
| [`vendor-research`](./skills/vendor-research/) | Identify comparable vendors and buyer situations. | OpenSEO connector, coordinator or supplied evidence |
| [`search-demand`](./skills/search-demand/) | Analyse search intent and buyer language. | OpenSEO connector, coordinator or supplied evidence |
| [`competitor-ad-research`](./skills/competitor-ad-research/) | Analyse competitor creative, offers and landing pages. | Via coordinator |
| [`creator-community-research`](./skills/creator-community-research/) | Map relevant creators, communities and recurring questions. | Via coordinator |
| [`avatar-synthesis`](./skills/avatar-synthesis/) | Build testable buyer profiles from cited evidence. | None |
| [`experiment-feedback`](./skills/experiment-feedback/) | Validate profiles against owned experiment outcomes. | Via coordinator or supplied outcomes |

`scenario-simulate` is synthetic by construction. Its output must never be
presented as observed population measurement.

For the full audience workflow, explicitly select all seven audience packages.
Deployed Compute agents receive only selected Vault bindings. For Treg collection,
bind its credential to `TREG_TOKEN` and use an explicit endpoint policy; start
with a zero budget and empty allowlist until those limits are supplied. Missing owned outcomes remain
`needs_input`; competitor longevity is not proof of profitability. Vendor/search stages
also work alone with supplied evidence or the attached OpenSEO connector. These
packages do not contain a direct OpenSEO API client.

Offline verification: `python3 -m unittest discover -s tests -v`.

## Import into a Stimulir workspace

In the Console, discover this repository and import only the skills the
workspace needs. The import is pinned to a resolved commit, and each managed
run materializes the selected package into the workspace sandbox.

```bash
stimulir skills discover stimulir/managed-skills --ref main
stimulir skills import stimulir/managed-skills \
  --path skills/web-scrape \
  --path skills/deep-research \
  --ref main
```

The sandbox installs each package from its own `pyproject.toml`. Deployed Compute
agents receive only their selected Vault bindings. Helpers such as Serper/Treg
read the bound environment variable (`SERPER_API_KEY` / `TREG_TOKEN`); connector
credentials stay on the backend. Never print credential values.

### OpenSEO in Agent Builder

Save an OpenSEO API key in the intended project's organization Vault, commonly
as `OPENSEO_API_KEY`. Add the **OpenSEO** connector block in the new Agent Builder,
verify the connection, select an OpenSEO project and grant the tools needed.
Save and publish the new agent version. Do not add the same key as a sandbox
credential. Quick Create/Edit carry the same connector grants.

The runtime provides `openseo_tools` and `openseo_call`; skills supply the
workflow and evidence rules. Call the catalog first, use its real schemas and
omit `projectId` from call arguments because the host injects the pinned provider
project. The Stimulir workspace ID is separate. Start with a context-only check;
run keyword/SERP/domain research only when requested. The selected OpenSEO
project must match the researched product. A Stimulir context is not LightReel
research evidence. OpenSEO research can use account credits; the Treg helper's
budget is separate.

The Console backend and Agent OS runtime must include connector support; older
runtimes and deployments without the block can still use supplied exports.
Skills are imported at an immutable commit. Publishing this repository does
not update existing imports or deployed versions: re-import/update the affected
skills at the reviewed commit, then save and publish a new agent version.

Reference: [OpenSEO MCP documentation](https://openseo.so/docs/mcp).

## Install in a coding agent

The catalog is also discoverable by skill-aware coding agents:

```bash
npx skills add stimulir/managed-skills
```

This is useful for local development and forward testing. Production managed
execution should use the workspace import flow above.

## Runtime contract

Every package is marked `metadata.category: managed` because the Stimulir
importer uses that category to distinguish sandbox capabilities from operator
skills. A managed skill:

- runs inside the workspace sandbox;
- reads explicitly bound helper credentials from its environment or uses attached
  host tools whose connector credentials remain server-side;
- remains bounded and resumable when work exceeds one run;
- writes outputs to the task's durable storage location;
- never assumes a `~/.stimulir` human session.

## Repository layout

```text
managed-skills/
├── .claude-plugin/plugin.json
├── .codex-plugin/plugin.json
└── skills/
    ├── deep-research/
    ├── opposition-enrich/
    ├── scenario-simulate/
    └── web-scrape/
```

Each skill owns its instructions, helper scripts, and Python dependencies.
There is intentionally no repository-root Python environment.
