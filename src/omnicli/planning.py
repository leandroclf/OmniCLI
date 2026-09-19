from __future__ import annotations

import hashlib
from typing import Any

from omnicli.config import config_fingerprint
from omnicli.models import OmniConfig
from omnicli.pipeline import RefinementSettings


def build_execution_plan(
    config: OmniConfig,
    idea: str,
    loops: int,
    refine: bool | None = None,
) -> dict[str, Any]:
    """Build a provider-free, reproducible description of a planned run."""
    normalized_idea = idea.strip()
    if not normalized_idea:
        raise ValueError("A ideia inicial não pode ser vazia")
    if loops < 1 or loops > config.pipeline.max_loops:
        raise ValueError(f"--loops deve estar entre 1 e {config.pipeline.max_loops}")
    settings = RefinementSettings.from_config(config.pipeline.quality_loop, enabled=refine)
    stage_names = [stage.name for stage in config.pipeline.stages]
    nominal_steps = loops * len(stage_names)
    return {
        "graph_version": config.pipeline.graph_version,
        "pipeline": config.pipeline.name,
        "execution_mode": "refinement" if settings.enabled else "linear",
        "loops": loops,
        "stages": stage_names,
        "providers": [stage.provider for stage in config.pipeline.stages],
        "nominal_steps": nominal_steps,
        "maximum_steps": settings.max_steps if settings.enabled else nominal_steps,
        "maximum_provider_calls": settings.max_calls if settings.enabled else nominal_steps,
        "input_retention": config.pipeline.input_retention.value,
        "idea_sha256": hashlib.sha256(normalized_idea.encode("utf-8")).hexdigest(),
        "config_fingerprint": config_fingerprint(config),
        "provider_free": True,
        "human_review_required": True,
    }
