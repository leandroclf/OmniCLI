from omnicli.lab import run_all_offline_checks, run_provider_contract_lab, run_synthetic_evaluation


def test_provider_contract_lab_is_deterministic_and_local() -> None:
    results = run_provider_contract_lab()

    assert results
    assert all(result.passed for result in results)
    assert {result.name for result in results} >= {"argv-transport", "timeout-cleanup", "output-limit"}


def test_synthetic_quality_corpus_is_not_a_human_benchmark() -> None:
    results = run_synthetic_evaluation()

    assert all(result.passed for result in results)


def test_offline_summary_explicitly_marks_external_gates_pending() -> None:
    result = run_all_offline_checks()

    assert result["passed"] is True
    assert result["authenticated_provider_compatibility"] == "not-tested"
    assert result["human_quality_benchmark"] == "not-tested"
