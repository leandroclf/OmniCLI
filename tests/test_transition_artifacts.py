import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]


def test_human_benchmark_is_versioned_and_covers_transition_cases() -> None:
    payload = yaml.safe_load((ROOT / "docs/benchmarks/human-quality-v1.yaml").read_text(encoding="utf-8"))

    assert payload["version"] == "human-quality-v1"
    assert payload["status"] == "prepared-not-executed"
    assert len(payload["dimensions"]) == 6
    assert len(payload["cases"]) == 8
    assert len({case["id"] for case in payload["cases"]}) == 8
    assert all(case["minimum"] and case["critical_failures"] for case in payload["cases"])


def test_provider_matrix_is_explicitly_pending_real_validation() -> None:
    payload = yaml.safe_load((ROOT / "docs/provider-compatibility-matrix.yaml").read_text(encoding="utf-8"))

    assert payload["version"] == "provider-compatibility-v1"
    assert payload["status"] == "partial-execution"
    assert payload["execution_policy"]["authentication_required"] is True
    assert {provider["status"] for provider in payload["providers"]} == {
        "partial",
        "out-of-scope",
        "deferred-next-stage",
    }
    assert "cli_version" in payload["required_evidence"]
    assert "rollback_procedure" in payload["required_evidence"]


def test_transition_report_schema_keeps_external_gates_explicit() -> None:
    payload = json.loads((ROOT / "docs/transition-report.schema.json").read_text(encoding="utf-8"))

    assert payload["properties"]["report_version"]["const"] == "transition-report-v1"
    assert "authenticated_provider_compatibility" in payload["required"]
    assert "human_quality_benchmark" in payload["required"]
