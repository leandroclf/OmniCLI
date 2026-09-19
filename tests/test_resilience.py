from pathlib import Path

import pytest

from omnicli.adapters.base import ProviderAdapter, ProviderResponse
from omnicli.config import DEFAULT_CONFIG
from omnicli.exceptions import PipelineError
from omnicli.pipeline import PipelineRunner


class CountingAdapter(ProviderAdapter):
    def __init__(self, name: str) -> None:
        self.provider_name = name
        self.calls = 0

    def check(self) -> str:
        return "synthetic 1.0"

    def run(self, prompt: str, timeout_seconds: float) -> ProviderResponse:
        self.calls += 1
        return ProviderResponse(
            stdout="# Escopo\n# Riscos\n# Critérios\n# Decisões\n" + ("detalhe " * 20),
            stderr="",
            exit_code=0,
        )


def test_refinement_stops_at_max_calls_before_unbounded_execution(tmp_path: Path) -> None:
    config = DEFAULT_CONFIG.model_copy(deep=True)
    config.pipeline.quality_loop.max_calls = 1
    adapters = {name: CountingAdapter(name) for name in config.providers}

    with pytest.raises(PipelineError, match="max_calls"):
        PipelineRunner(config, adapters).run(
            "Uma ideia",
            loops=3,
            refine=True,
            workspace_root=tmp_path / "workspace",
            output=tmp_path / "proposal.md",
        )

    assert sum(adapter.calls for adapter in adapters.values()) == 1


def test_refinement_stops_at_max_steps_before_executing_next_stage(tmp_path: Path) -> None:
    config = DEFAULT_CONFIG.model_copy(deep=True)
    config.pipeline.quality_loop.max_steps = 1
    adapters = {name: CountingAdapter(name) for name in config.providers}

    with pytest.raises(PipelineError, match="max_steps"):
        PipelineRunner(config, adapters).run(
            "Uma ideia",
            loops=3,
            refine=True,
            workspace_root=tmp_path / "workspace",
            output=tmp_path / "proposal.md",
        )

    assert sum(adapter.calls for adapter in adapters.values()) == 1
