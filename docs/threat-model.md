# Threat model

## Scope

OmniCLI launches locally installed AI CLIs, passes text between stages, and stores run artifacts. It does not sandbox providers, execute generated code, or manage provider credentials.

## Trust boundaries

| Boundary | Risk | Current control |
|---|---|---|
| User input → provider | Prompt injection, sensitive data disclosure | Inputs are marked as untrusted; prompts forbid role changes, secret disclosure, commands, and external actions |
| Provider output → next provider | Instruction propagation and poisoned context | Previous output is delimited as data and challenged by critical-review stages |
| OmniCLI → local process | Command injection or unexpected interactive mode | Argument lists without a shell; explicit `{prompt}` transport; timeouts; documented headless commands |
| Process → local environment | Credential or file access inherited from the user | No privilege elevation; warning that OmniCLI is not a sandbox; provider environments are explicit additions |
| Run → workspace | Sensitive prompt/output retention | Prompt content retention disabled by default; isolated run directory; manifest hashes support audit without storing prompt text |
| Configuration → execution | Malicious executable or environment override | Strict schema and no shell strings; users must review untrusted configuration before execution |

## Residual risks

- Prompt injection defenses are probabilistic and can fail.
- Provider CLIs may read local context or configuration according to their own behavior.
- Prompt text passed in process arguments may be observable to same-host process inspection on some systems.
- Output can contain malicious commands, links, or code even when the provider was instructed otherwise.
- Provider services receive content under their own privacy and retention policies.

## Required controls before implementation mode

- Isolated temporary Git worktree or container.
- Explicit allowlist for executable commands and writable paths.
- Diff preview and human approval before repository mutation.
- Secret scanning before prompts leave the machine and before patches are applied.
- Resource limits, network policy, test gates, rollback, and append-only audit events.
- Red-team cases for indirect prompt injection and malicious repository content.

Security vulnerabilities should be reported according to [SECURITY.md](../SECURITY.md).
