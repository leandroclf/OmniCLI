# Project landscape and product decisions

Research date: 2026-09-19. Sources are official project repositories and vendor documentation. Feature availability can change; provider commands must be checked before each compatibility release. See [provider-compatibility.md](../provider-compatibility.md) for the executable contract and maintenance policy.

## Comparable projects

| Project | Proven strength | Lesson for OmniCLI | What OmniCLI should not copy yet |
|---|---|---|---|
| [Aider](https://github.com/Aider-AI/aider) | Repository maps, Git-native edits, automatic lint/test loops, broad model support, mature docs | Make outcomes reproducible, integrate quality checks, and invest in excellent onboarding | Competing as another full coding agent before the conception workflow is reliable |
| [LLM](https://github.com/simonw/llm) | Small composable CLI, provider plugins, structured output, searchable prompt/response history | Keep the core narrow and establish an extension contract plus optional provenance stores | Persisting all conversations by default, which conflicts with OmniCLI's privacy posture |
| [Claude Squad](https://github.com/smtg-ai/claude-squad) | Multiple agents in isolated Git worktrees, background sessions, review-before-apply | Future implementation workflows should use isolation, diffs, and human approval | Parallel agents for conception, where sequential context and editorial accountability are the product essence |
| [OpenHands](https://github.com/OpenHands/OpenHands) | Multi-agent/back-end control center, integrations and automations | Provide observability and reusable workflow packs as adoption grows | A broad platform scope that would dilute the initial CLI value proposition |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | Headless output formats, checkpointing, sandbox and telemetry controls | Prefer documented non-interactive contracts and explicit diagnostics | Depending on undocumented terminal behavior |
| [Codex CLI](https://github.com/openai/codex) | Local terminal agent with explicit non-interactive execution | Treat each provider as a versioned adapter contract | Assuming all tools consume prompts the same way |
| [Claude Code](https://github.com/anthropics/claude-code) | Terminal-native agent, programmatic mode and extension ecosystem | Keep official installation and invocation guidance current | Coupling OmniCLI to one vendor's agent model |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-copilot-cli) | Standalone CLI with documented `-p`/`--prompt`, approval-oriented tools and MCP extension | Use the documented prompt mode, probe the installed help surface, and retain explicit approval | Retaining the obsolete `gh copilot` extension command or enabling `--allow-all-tools`/`--yolo` |

## Critical assessment of the original proposal

### Strong and defensible

- Coordinating already-authenticated local CLIs is simpler for users who already have provider subscriptions.
- Sequential refinement is a clear product identity and maps well to turning ambiguous intent into an RFC-like artifact.
- Markdown artifacts and a resumable workspace make the workflow inspectable.
- Provider neutrality can produce better review diversity than a single-model workflow.

### Claims that required correction

- **“Zero-token cost” is not accurate.** Usage consumes provider quotas and may require paid subscriptions. The defensible claim is “no OmniCLI-managed API keys or usage billing.”
- **Blind “yes, and” prompting amplifies errors.** Constructive continuity must be paired with explicit criticism, uncertainty labels, and pending decisions.
- **Raw stdin/stdout is not a universal protocol.** Gemini, Claude, and Codex document different headless invocation shapes. Compatibility must be tested and versioned.
- **Official CLIs can change.** Local subprocess orchestration avoids REST schema coupling, but it is not immune to command, output, authentication, or licensing changes.
- **Local execution is not automatically private.** Prompts can still be sent to provider services, and child processes inherit user permissions and environment.

## Prioritized evolution

### P0 — reliability and trust

- [x] Official headless command shapes for Gemini, Claude, and Codex.
- [x] `omnicli doctor` with JSON output for automated readiness checks.
- [x] Shell-free execution, prompt-size limits, and opt-in execution for uncertain integrations.
- [x] Prompt/output hashes and prompt-injection boundaries.
- [x] Safe, reproducible bootstrap and multi-version CI.
- [x] Version/capability probes with an official-source registry and optional URL check.
- [ ] Provider contract tests against pinned real CLI versions in an opt-in compatibility workflow.

### P1 — community usefulness

- Reusable, versioned pipeline packs such as idea-to-RFC, architecture review, threat modeling, and ADR review.
- A documented provider/plugin interface with compatibility metadata.
- Evaluation fixtures that measure completeness, contradiction detection, unresolved decisions, latency, and successful-task cost.
- English and Portuguese documentation with a translation contribution path.
- Opt-in, privacy-preserving diagnostics; never collect prompt content or telemetry by default.

### P2 — controlled implementation

- Isolated Git worktrees and patch-only changes.
- Human approval before applying a diff or running generated commands.
- Policy-controlled tests, rollback, and auditable repair attempts.
- Parallel execution only where tasks are independent and convergence is explicit.

## Adoption strategy

Repository popularity cannot be guaranteed or engineered honestly through features alone. The project should optimize for evidence of usefulness:

1. A new user reaches a successful proposal quickly and can diagnose failures alone.
2. Example outputs demonstrate when multiple providers improve a decision.
3. Releases publish compatibility status and migration notes.
4. Maintainers respond predictably to issues and recognize contributors.
5. Public evaluations show quality improvements instead of relying on marketing claims.

Recommended metrics are successful first run, pipeline completion rate, time to diagnosis, repeat usage, contributor retention, and issue response time. Stars are a lagging signal—not the product objective.
