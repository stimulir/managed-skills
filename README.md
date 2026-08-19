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

`scenario-simulate` is synthetic by construction. Its output must never be
presented as observed population measurement.

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

The sandbox installs each package from its own `pyproject.toml`. Research
skills read `SERPER_API_KEY` from the workspace Vault. The platform currently
makes the workspace Vault available to the sandbox as a whole, so skills must
read only the variables they need and must never print secret values.

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
- reads credentials only from its environment;
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

