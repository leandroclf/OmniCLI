# Changelog

## Unreleased

- Check provider CLI versions, declared headless capabilities, and official
  latest stable metadata before live pipeline runs; warn by default and provide
  a strict `--require-latest` gate without silently updating user installations.

## Unreleased

- Added aggregated run metrics for duration, failures, retries, output volume and context growth.
- Added release checksums and CycloneDX SBOM generation to the release workflow.
- Added a gate-by-gate production transition status document that keeps authenticated-provider and human-benchmark evidence explicit.
- Adjusted the Codex stderr budget for verbose operational output without changing stdout or prompt limits.
- Restricted the production-validation default pipeline to Claude Code and Codex CLI; Gemini is deferred to a later stage.

All notable changes to this project will be documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project intends to follow [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-09-19

### Added

- Secure hash-only input retention by default, with validated resume input.
- Redacted configuration snapshots and configuration fingerprints.
- Workspace path containment, restrictive permissions, advisory locks, and atomic manifests.
- Provider environment allowlists, bounded output capture, process-group termination, and call budgets.
- Deterministic quality evidence and versioned quality reports.

### Security

- Rejected path traversal and absolute run identifiers.
- Prevented configured environment values from being persisted in manifests.
- Added regression tests for workspace escape, permissions, secret redaction, output limits, and resume integrity.

## [0.4.0] - 2026-09-19

### Added

- Provider-free `conceive --dry-run --json` execution plans.
- Offline diagnostics with `doctor --offline` and `providers check --offline`.
- Local provider contract laboratory for transport, capability probes, exits, timeouts and output limits.
- Deterministic synthetic quality corpus exposed by `omnicli lab evaluate` and `omnicli lab verify`.
- JSON run inspection and versioned manifest schema validation.
- Atomic writes for stage artifacts in addition to atomic manifests.

### Validation boundaries

- Offline checks do not authenticate providers or prove vendor compatibility.
- Synthetic quality evaluation does not replace human review or a human quality benchmark.

## [Unreleased]

### Changed

- Added optional local/Git codebase inspection, bounded context preview and
  provenance checks on resume; aligned README with the Claude/Codex default.

### Planned

- Reusable pipeline packs and proposal-quality evaluations.

### Added

- Opt-in `--refine` mode with bounded conditional routing after the master proposal.
- Deterministic quality-gate signals, best-result preservation, and explicit termination reasons in run manifests.
- Official provider compatibility registry, safe help-surface capability probes, and optional bootstrap URL checks.

### Security

- Enforced `setuptools>=83.0.0` in development and bootstrap environments after dependency auditing identified a vulnerable older release.

### Documentation

- Added the post-validation production transition plan with phase gates,
  evidence requirements, pilot criteria and the productive-release checklist.

## [0.2.0] - 2026-09-19

### Added

- `omnicli doctor` with table or JSON readiness output.
- Safe prompt transport through an isolated `{prompt}` argument or `stdin`.
- Prompt-size limits and SHA-256 provenance fields in run manifests.
- Prompt-injection boundaries between chained provider outputs.
- Competitive research, threat model, roadmap, community templates, and bilingual onboarding.
- Dependabot and automated GitHub release packaging.

### Changed

- Default provider commands now match documented Gemini, Claude, and Codex headless interfaces.
- Default provider contracts now include documented Claude output mode and GitHub Copilot `-p` prompt mode; Copilot remains outside the default stage pipeline.
- CI now runs type checking, dependency validation, CLI smoke tests, and package builds.

### Security

- Provider prompts are never interpolated into shell commands.
- Uncertain provider integrations are not invoked interactively or enabled in the stage pipeline.

## [0.1.0] - 2026-09-19

### Added

- Configurable conception pipeline, local subprocess adapter, resumable workspaces, preliminary quality report, tests, CI, and safe bootstrap.

[Unreleased]: https://github.com/leandroclf/OmniCLI/commits/main
[0.3.0]: https://github.com/leandroclf/OmniCLI/commits/main
[0.4.0]: https://github.com/leandroclf/OmniCLI/commits/main
[0.2.0]: https://github.com/leandroclf/OmniCLI/commits/main
[0.1.0]: https://github.com/leandroclf/OmniCLI/commit/babe5aef2879570d5f888089bd1ce5e29a348dff
