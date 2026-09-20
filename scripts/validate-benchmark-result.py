#!/usr/bin/env python3
"""Validate one blinded human benchmark result."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

EXPECTED_DIMENSIONS = {
    "completeness",
    "technical_coherence",
    "factual_discipline",
    "risk_security",
    "decision_traceability",
    "developer_utility",
}
DECISIONS = {"approved", "approved-with-reservations", "rejected", "needs-review"}
FORBIDDEN_BLINDING_KEYS = {"provider", "model", "vendor", "provider_name", "model_name"}
REQUIRED_ARTIFACTS = {"manifest", "final_output", "stage_outputs", "prompt_artifacts", "config_fingerprint"}


def _errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "result_version",
        "benchmark_version",
        "case_id",
        "blind_run_id",
        "evaluator_id",
        "reviewed_at",
        "review_time_minutes",
        "artifact_refs",
        "dimensions",
        "critical_failures",
        "observations",
        "disagreements",
        "decision",
    }
    errors.extend(f"campo obrigatório ausente: {key}" for key in sorted(required - payload.keys()))
    if payload.get("result_version") != "human-quality-result-v1":
        errors.append("result_version deve ser human-quality-result-v1")
    if not isinstance(payload.get("review_time_minutes"), int) or payload.get("review_time_minutes", 0) < 0:
        errors.append("review_time_minutes deve ser um inteiro não negativo")
    if payload.get("decision") not in DECISIONS:
        errors.append(f"decision deve ser uma destas opções: {', '.join(sorted(DECISIONS))}")
    artifact_refs = payload.get("artifact_refs")
    if not isinstance(artifact_refs, dict):
        errors.append("artifact_refs deve ser um objeto")
    else:
        errors.extend(
            f"evidência obrigatória ausente: {key}"
            for key in sorted(REQUIRED_ARTIFACTS - artifact_refs.keys())
        )
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, list):
        errors.append("dimensions deve ser uma lista")
    else:
        seen: set[str] = set()
        for index, dimension in enumerate(dimensions):
            if not isinstance(dimension, dict):
                errors.append(f"dimensions[{index}] deve ser um objeto")
                continue
            identifier = dimension.get("id")
            seen.add(identifier)
            score = dimension.get("score")
            if not isinstance(score, int) or not 0 <= score <= 4:
                errors.append(f"nota inválida para {identifier}: use um inteiro de 0 a 4")
            if not isinstance(dimension.get("evidence"), str) or not dimension["evidence"].strip():
                errors.append(f"evidence ausente para {identifier}")
        if seen != EXPECTED_DIMENSIONS:
            errors.append(f"dimensões devem ser exatamente: {', '.join(sorted(EXPECTED_DIMENSIONS))}")
    if payload.get("critical_failures") and payload.get("decision") == "approved":
        errors.append("uma proposta com falhas críticas não pode ter decision=approved")
    serialized = json.dumps(payload, ensure_ascii=False, default=str).casefold()
    for key in FORBIDDEN_BLINDING_KEYS:
        if f'"{key}"' in serialized or f"'{key}'" in serialized:
            errors.append(f"identificador proibido para cegamento: {key}")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: validate-benchmark-result.py RESULT.yaml", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 1
    if not isinstance(payload, dict):
        print(json.dumps({"valid": False, "errors": ["resultado deve ser um objeto YAML"]}, ensure_ascii=False))
        return 1
    errors = _errors(payload)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
