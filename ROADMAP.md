# Roadmap

The roadmap protects OmniCLI's core idea: improve human–AI communication through transparent, sequential, multi-provider refinement. Dates are intentionally omitted until maintainers have enough delivery data.

## 0.2 — Trustworthy local orchestration

- [x] Documented headless invocations for Gemini, Claude, and Codex.
- [x] Safe `argv`/`stdin` prompt transport without a shell.
- [x] Readiness diagnostics with human and JSON output.
- [x] Prompt-size limits, prompt-injection boundaries, and artifact hashes.
- [x] Safe bootstrap, CI matrix, packaging checks, and dependency automation.
- [x] Research, threat model, bilingual onboarding, and community files.
- [x] Bounded opt-in quality loop with deterministic routing and explicit termination reasons.
- [x] Official provider source registry, version checks, and safe capability probes.

## 0.3 — Secure controlled beta foundation

- [x] Workspace containment, restrictive permissions, atomic manifests, and locks.
- [x] Hash-only input retention, redacted snapshots, and resume integrity checks.
- [x] Provider environment allowlists, output limits, timeout process cleanup, and call budgets.
- [x] Versioned deterministic quality evidence and production-readiness gates.
- [x] Security regression coverage and operational documentation.

## 0.4 — Pipeline packs and evaluations

- [ ] Versioned packs for idea-to-RFC, architecture review, threat modeling, and ADR review.
- [x] Versioned manifest schema with forward-version rejection.
- [x] Deterministic provider contract fixtures and synthetic quality evaluation.
- [x] Provider-free planning, offline diagnostics and JSON run inspection.
- [x] Atomic stage artifacts and bounded subprocess failure laboratory.
- [ ] Run metrics for latency, failures, retries, and context growth.
- [ ] Compatibility matrix generated from opt-in provider contract tests across pinned provider versions.

## 0.5 — Extension ecosystem

- [ ] Documented provider adapter API and entry-point discovery.
- [ ] Provider capability metadata and graceful fallback policies.
- [ ] Pipeline pack registry format with local-first installation.
- [ ] Translation workflow and contributor documentation.

## 1.0 — Stable conception workflow

- [ ] Stable configuration and manifest schemas with migration support.
- [ ] Reproducible releases and compatibility policy.
- [ ] Quality gates backed by public evaluation data.
- [ ] Complete operational and security documentation.

## After 1.0 — Controlled implementation

- [ ] Isolated Git worktrees and patch-only changes.
- [ ] Diff review and explicit approval before applying changes.
- [ ] Command/path allowlists, secret scanning, test gates, and rollback.
- [ ] Auditable repair loops with strict attempt and resource limits.

Parallel agent execution is not a goal by itself. It will be introduced only when it improves an evaluated workflow without weakening accountability or increasing context waste.
