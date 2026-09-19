# Contributing to OmniCLI

Thank you for helping improve communication between people and AI tools. Contributions do not need to be large: provider compatibility reports, documentation fixes, examples, translations, and evaluation cases are especially useful.

## Before opening a change

1. Search existing issues and the [roadmap](ROADMAP.md).
2. Open a feature request before large architectural work.
3. Never include credentials, proprietary prompts, personal data, or provider output you cannot redistribute.
4. Keep changes focused and preserve the local-first, human-reviewable design.

## Local setup

```bash
bash scripts/bootstrap.sh --apply --check
source .venv/bin/activate
omnicli --help
```

Before submitting a pull request:

```bash
ruff check .
pytest --cov=omnicli --cov-report=term-missing
mypy
python -m pip check
python -m build
```

Tests that call paid or authenticated providers must be opt-in and clearly labeled. The default test suite must remain deterministic and offline.

## Design rules

- Do not invoke a shell for provider prompts.
- Do not add undocumented provider flags as defaults.
- Do not persist prompts, secrets, or telemetry by default.
- Treat model output as untrusted input.
- Require human approval before generated code or commands can mutate a repository.
- Add tests and migration notes when configuration or manifest schemas change.

## Pull requests

Explain the problem, the chosen trade-off, validation performed, security/privacy impact, and documentation changes. Small, reviewable commits are preferred. By contributing, you agree that your work is licensed under the project's MIT license.

Community behavior is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report vulnerabilities privately according to [SECURITY.md](SECURITY.md).
