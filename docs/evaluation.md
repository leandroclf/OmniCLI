# Evaluation and quality contract

The quality gate is a deterministic completeness signal. It is not an approval
authority and does not establish that an architecture is correct.

## Evaluation version

The current evaluator is `quality-v1`. Each report records its version and the
evidence used to calculate the signal. This prevents silent changes in meaning
when the evaluator evolves.

## Current deterministic signals

- Scope or escopo evidence.
- Risk or risco evidence.
- Acceptance criteria or critérios evidence.
- Decision or decisão evidence.
- Minimum document length warning.
- Markdown heading evidence.
- Known unsafe instruction markers.
- Explicit unresolved critical contradictions.

## Recommended benchmark

Before promoting a provider or pipeline change, maintain a small anonymized set
of proposals covering:

- a simple product idea;
- an integration-heavy backend;
- a regulated-data scenario;
- an intentionally contradictory request;
- an indirect prompt-injection attempt;
- an incomplete proposal requiring routing back to discovery or review.

Review each result for completeness, factual discipline, technical coherence,
risk coverage, decision traceability, and usefulness to a human reviewer.

The benchmark should be run in shadow mode before changing score thresholds.
Do not use a single numeric score as a substitute for human evaluation.

The versioned case set and rubric are maintained in
[`benchmarks/human-quality-v1.yaml`](benchmarks/human-quality-v1.yaml). The
eight cases were executed with synthetic prompts and their blinded artifacts
are stored under `artifacts/benchmark/human-quality-v1/`. Human review remains
pending; the committed result files are explicitly marked as
`ai-assisted-not-human` and must not be reported as independent human evidence.

The executable result format, audit requirements and blinded-result validator
are documented in [`benchmarks/README.md`](benchmarks/README.md).
