# Offline verification

This document defines what can be verified before authenticated provider CLIs
and human reviewers are available.

## Commands

```bash
omnicli conceive "A product idea" --dry-run --json
omnicli doctor --offline --json
omnicli providers check --offline
omnicli lab providers --json
omnicli lab evaluate --json
omnicli lab verify --json
```

## What is covered

The provider laboratory uses local deterministic Python processes to exercise:

- isolated `argv` and `stdin` prompt transport;
- version and capability probes;
- non-zero exit codes;
- timeout and process cleanup;
- bounded provider output.

The synthetic corpus exercises the `quality-v1` evaluator with complete,
incomplete, unsafe and contradictory documents. It checks routing and hard
gates, but is not a human quality benchmark.

The dry-run plan checks the fixed conception topology, configured providers,
loop bounds, refinement bounds, hash-only input retention and configuration
fingerprint without invoking any external CLI.

## Evidence boundaries

Passing offline verification means that the local OmniCLI behavior is
reproducible for the covered cases. It does not prove:

- a provider CLI is installed or authenticated;
- a vendor's current headless interface is compatible;
- a model produces technically correct architecture;
- adaptive routing is better than linear execution;
- the workflow is ready for unrestricted production use.

Those claims require opt-in provider compatibility tests and review by human
evaluators. Until then, `strategy=linear` remains the default and prompts are
not retained by default.
