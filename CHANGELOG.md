# Changelog

All notable changes to this project will be documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project intends to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned

- Reusable pipeline packs and proposal-quality evaluations.

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
- GitHub Copilot now uses the standalone `copilot` command and is disabled by default until a stable headless invocation is configured.
- CI now runs type checking, dependency validation, CLI smoke tests, and package builds.

### Security

- Provider prompts are never interpolated into shell commands.
- Uncertain provider integrations are disabled rather than invoked interactively.

## [0.1.0] - 2026-09-19

### Added

- Configurable conception pipeline, local subprocess adapter, resumable workspaces, preliminary quality report, tests, CI, and safe bootstrap.

[Unreleased]: https://github.com/leandroclf/OmniCLI/commits/main
[0.2.0]: https://github.com/leandroclf/OmniCLI/commits/main
[0.1.0]: https://github.com/leandroclf/OmniCLI/commit/babe5aef2879570d5f888089bd1ce5e29a348dff
