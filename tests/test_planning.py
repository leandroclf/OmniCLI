from omnicli.config import DEFAULT_CONFIG
from omnicli.planning import build_execution_plan


def test_execution_plan_is_provider_free_and_bounded() -> None:
    plan = build_execution_plan(DEFAULT_CONFIG, "Uma ideia", loops=2)

    assert plan["provider_free"] is True
    assert plan["execution_mode"] == "linear"
    assert plan["nominal_steps"] == 10
    assert plan["maximum_provider_calls"] == 10
    assert len(plan["idea_sha256"]) == 64


def test_refinement_plan_uses_configured_bounds() -> None:
    config = DEFAULT_CONFIG.model_copy(deep=True)
    config.pipeline.quality_loop.enabled = True
    config.pipeline.quality_loop.max_steps = 7
    config.pipeline.quality_loop.max_calls = 9

    plan = build_execution_plan(config, "Uma ideia", loops=3, refine=None)

    assert plan["execution_mode"] == "refinement"
    assert plan["maximum_steps"] == 7
    assert plan["maximum_provider_calls"] == 9
