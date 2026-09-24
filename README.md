# OmniCLI

[![CI](https://github.com/leandroclf/OmniCLI/actions/workflows/ci.yml/badge.svg)](https://github.com/leandroclf/OmniCLI/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Controlled Beta](https://img.shields.io/badge/status-controlled%20beta-blue.svg)](docs/production-readiness.md)

**Turn one rough idea into a reviewable engineering proposal by chaining the AI CLIs you already use.**

OmniCLI is a local, configurable orchestrator for authenticated command-line AI tools. Its first workflow passes an idea through product discovery, critical review, architecture, feasibility, and technical editing—while preserving artifacts and provenance for human review.

> OmniCLI does not promise “free AI.” It does not require its own API keys, but every provider remains subject to its subscription, quota, licensing, privacy, and acceptable-use terms.

[Leia em Português](docs/README.pt-BR.md) · [Interface screenshots](docs/interface.md) · [Architecture](docs/architecture.md) · [Provider compatibility](docs/provider-compatibility.md) · [Research](docs/research/landscape.md) · [Roadmap](ROADMAP.md)

For the practical use of OmniCLI in a software engineering process, including
workflow placement, use cases, expected benefits and current limitations, see
the [engineering workflow guide](docs/fluxo-engenharia.md) (Portuguese).

Production criteria: [readiness](docs/production-readiness.md) · [production transition plan](docs/plano-transicao-producao.md) · [evaluation contract](docs/evaluation.md) · [release process](docs/release.md)

For an existing project, use [optional codebase context](docs/codebase-context.md)
to preview selected source excerpts before generating a grounded proposal.

## Why OmniCLI?

Most agent tools focus on writing code. OmniCLI focuses first on the communication problem that comes before code: turning ambiguous intent into an explicit, challenged, and traceable engineering plan.

- **Bring your own CLI:** use locally installed and authenticated tools; OmniCLI stores no provider credentials.
- **Constructive disagreement:** stages challenge assumptions instead of blindly continuing a “yes, and” chain.
- **Human-readable artifacts:** every stage produces Markdown and a manifest suitable for review and audit.
- **Provider-neutral pipelines:** roles, instructions, timeouts, retries, and providers live in YAML.
- **Safe by default:** no shell execution, automatic code execution, repository mutation, or prompt persistence by default.
- **Recoverable runs:** inspect or resume interrupted workflows without discarding completed stages.

OmniCLI 0.4 is a controlled beta foundation. The current workflow is suitable for
technical pilots with reviewed, non-sensitive material. It is not a sandbox and
does not execute generated code or mutate repositories.

## 60-second start

Requirements: Linux, Python 3.10+, and the provider CLIs required by your pipeline.

```bash
git clone https://github.com/leandroclf/OmniCLI.git
cd OmniCLI
bash scripts/bootstrap.sh --apply --check
source .venv/bin/activate
omnicli doctor --capabilities
```

The bootstrap creates a local virtual environment and configuration. It never uses `sudo`, installs provider CLIs, or contacts a model unless you explicitly pass `--idea`.

After installing and authenticating Claude Code and Codex CLI:

```bash
omnicli conceive \
  "A gamified meditation app with RPG progression" \
  --loops 1 \
  --output architecture-proposal.md \
  --preview
```

## Official default invocations

The current default pipeline uses the documented headless interfaces of Claude Code and Codex CLI.

| Provider | Default invocation shape | Default state |
|---|---|---|
| Gemini CLI | `gemini -p "{prompt}" --output-format text` | deferred; custom configuration only |
| Claude Code | `claude -p "{prompt}" --output-format text` | enabled |
| Codex CLI | `codex exec "{prompt}"` | enabled |
| GitHub Copilot CLI | `copilot -p "{prompt}"` | out of scope; custom configuration only |

`{prompt}` is passed as one process argument without a shell. Custom tools can omit the placeholder to receive the prompt through `stdin`.

## Core commands

```bash
omnicli doctor [--json] [--skip-version] [--capabilities]
omnicli doctor --offline --json
omnicli providers check [--capabilities] [--latest] [--json]
omnicli lab verify [--json]
omnicli init omnicli.yaml
omnicli conceive "My idea" --config omnicli.yaml
omnicli conceive "My idea" --dry-run --json
omnicli conceive "My idea" --loops 3 --refine --output proposal.md
omnicli run inspect RUN_ID [--json]
omnicli run resume RUN_ID

# With the secure hash-only input retention default:
omnicli run resume RUN_ID --idea "The original idea"
```

`doctor --capabilities` validates the configuration, required executables, provider versions, and documented help markers without generating content. See [provider compatibility](docs/provider-compatibility.md) for the update policy; a passing probe is not a guarantee that every vendor feature is supported.

When provider authentication is unavailable, use `doctor --offline` for configuration-only validation and `omnicli lab verify` for deterministic local transport, failure-boundary and quality-regression checks. These commands explicitly do not claim authenticated-provider compatibility or human-evaluated quality.

Before a live pipeline run, OmniCLI checks provider versions and the configured
headless command markers, then compares installed versions with official
release metadata cached for 12 hours. It warns when an update is available;
`--require-latest` makes that check a gate. OmniCLI never replaces provider
installations automatically. Run `omnicli providers check --latest --json` for
current versions and official documentation/release links. See the
[provider compatibility policy](docs/provider-compatibility.md).

## Pipeline model

The default pipeline is deliberately sequential:

1. Product discovery with Claude.
2. Adversarial review with Codex.
3. Solution architecture with Codex.
4. Feasibility review with Claude.
5. Master proposal editing with Claude.

Each stage receives the original idea and the previous result. Inputs are delimited as untrusted data, and every prompt instructs the provider not to follow embedded attempts to change roles, reveal secrets, or execute commands. This is defense in depth—not a guarantee against prompt injection.

The default prompts preserve the predominant language of the original idea, and the quality check recognizes Portuguese and English proposal sections.

### Optional quality-driven refinement

The default behavior of `--loops` remains compatible: each loop runs the complete pipeline. Add `--refine` to turn `--loops` into a maximum number of proposal passes. After each `master-proposal`, OmniCLI runs a deterministic quality gate and routes only the needed suffix of the pipeline—for example, back to `critical-review` when risks or decisions are missing. It does not use another LLM as an opaque judge.

```bash
omnicli conceive \
  "A gamified meditation app with RPG progression" \
  --loops 3 \
  --refine \
  --output architecture-proposal.md \
  --verbose
```

The quality loop is also configurable in YAML:

```yaml
pipeline:
  quality_loop:
    enabled: false
    min_score: 80
    min_improvement: 3
    stable_passes: 1
    max_steps: 30
    max_calls: 50
    stop_on_quality: true
```

`min_score` is a completeness signal, not a promise of correctness. Hard gates block automatic acceptance when the output declares unresolved critical contradictions or contains known unsafe instruction markers. Every refined run records `quality_history`, `route_history`, `steps_used`, `calls_used`, `passes_completed`, `best_quality_score`, `graph_version`, and `termination_reason` in its manifest. A run can end by reaching the threshold, stabilizing, reaching a bound, or remaining blocked; human review is still required.

The production validation scope for this release is Claude Code and Codex CLI.
Gemini is deferred to a later stage, and Copilot is out of scope. See
[omnicli.example.yaml](omnicli.example.yaml) to customize the stages and providers.

### Offline verification

`conceive --dry-run` validates the pipeline shape, bounds, retention policy and configuration fingerprint without executing a provider or creating a workspace. The local laboratory can be run independently:

```bash
omnicli lab providers
omnicli lab evaluate
omnicli lab verify --json
```

The laboratory uses local synthetic processes. It validates OmniCLI's own subprocess contract, not vendor behavior, model quality, authentication, quotas or billing.

## Traceability and privacy

Every run creates an isolated workspace with stage outputs and `manifest.json`. The manifest records status, provider version, timestamps, output size, configuration fingerprint, and SHA-256 hashes of input, prompts, and outputs. Input content is not retained by default; `run resume` requires the original idea and validates its hash. Full stage prompt text is not retained unless `retain_prompt_content: true` is explicitly configured. Provider environment values are always redacted in the manifest.

Provider subprocesses run with the current user's permissions. The default environment is restricted to a small allowlist and configured values are passed only when explicitly declared. OmniCLI is an orchestrator, not a sandbox. Read the [production readiness](docs/production-readiness.md), [threat model](docs/threat-model.md), and [security policy](SECURITY.md) before using sensitive data.

## Project direction

The near-term priorities are reliable adapters, reusable pipeline packs, measurable proposal quality, internationalization, and a documented extension contract. Code implementation and self-healing remain gated behind isolated workspaces, diffs, tests, and explicit human approval.

The competitive analysis behind these choices is documented in [docs/research/landscape.md](docs/research/landscape.md). Stars are welcome, but activation success, reproducibility, contributor trust, and useful outputs are the product metrics.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports, provider compatibility reports, pipeline examples, translations, documentation, and evaluation cases are all valuable contributions.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Security issues should be reported privately according to [SECURITY.md](SECURITY.md).

## License

MIT © OmniCLI contributors. See [LICENSE](LICENSE).
