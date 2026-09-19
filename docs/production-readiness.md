# Production readiness

## Current position

OmniCLI 0.4 is a controlled beta foundation for local technical pilots. It is
not a sandbox, a hosted multi-tenant service, or an autonomous coding agent.
Generated documents remain untrusted and require human approval.

The complete post-validation execution sequence is documented in the
[production transition plan](plano-transicao-producao.md). It must be read
before promoting the tool beyond a controlled beta.

## Security controls implemented

- Run identifiers are restricted to safe names and remain inside the workspace.
- Workspace directories use restrictive permissions where supported.
- Manifest writes are atomic and serialized with an advisory lock.
- Input content is hash-only by default.
- Provider environment values are redacted from manifests.
- Provider environments use a minimal allowlist unless explicit inheritance is enabled.
- Provider prompts and outputs have configurable limits.
- Provider process groups are terminated on timeout on POSIX systems.
- Configuration fingerprints prevent silent configuration drift during resume.
- Call budgets and step budgets bound adaptive execution.

## Required before a production pilot

- Run adversarial tests for prompt injection and malicious provider output.
- Review provider privacy, retention, licensing, quota, and authentication terms.
- Use a dedicated operating-system account or container for sensitive workloads.
- Configure explicit environment variables instead of `inherit_environment`.
- Establish retention, deletion, incident response, and vulnerability handling procedures.
- Test provider contracts against pinned versions in an opt-in environment.
- Run `omnicli lab verify` in every change and release candidate.
- Run `omnicli doctor --offline` when provider authentication is unavailable.
- Publish signed release artifacts and a software bill of materials.
- Maintain a documented rollback path and a human approval checkpoint.

## Release gates

A release cannot be promoted to a production pilot unless all of the following
are true:

1. `pytest`, Ruff, mypy, build, and dependency checks pass.
2. Security regression tests pass.
3. No unredacted secret appears in a generated manifest.
4. Resume succeeds with the same configuration and rejects configuration drift.
5. Provider output limits and timeout behavior are verified.
6. A representative evaluation set has a reviewed baseline.
7. The release notes document migration and rollback impact.

## Explicit non-goals for 0.4

- Arbitrary shell or code execution.
- Automatic repository mutation.
- Autonomous tool selection or unbounded agent loops.
- Parallel execution solely for speed.
- Hosted storage of prompts or provider credentials.
- Treating synthetic provider contracts as vendor compatibility evidence.
- Treating the synthetic quality corpus as a human benchmark.
