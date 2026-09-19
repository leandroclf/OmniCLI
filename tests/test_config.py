from pathlib import Path

import pytest
from pydantic import ValidationError

from omnicli.config import DEFAULT_CONFIG, load_config, write_example_config
from omnicli.exceptions import ConfigurationError
from omnicli.models import OmniConfig, PipelineConfig, ProviderConfig, StageConfig


def test_default_config_has_critical_pipeline() -> None:
    names = [stage.name for stage in DEFAULT_CONFIG.pipeline.stages]
    assert names == [
        "discovery",
        "critical-review",
        "architecture",
        "feasibility",
        "master-proposal",
    ]
    assert DEFAULT_CONFIG.providers["gemini"].args[1] == "{prompt}"
    assert DEFAULT_CONFIG.providers["codex"].args[0] == "exec"
    assert DEFAULT_CONFIG.providers["claude"].args[-2:] == ["--output-format", "text"]
    assert DEFAULT_CONFIG.providers["copilot"].args == ["-p", "{prompt}"]
    assert DEFAULT_CONFIG.providers["copilot"].enabled
    assert DEFAULT_CONFIG.providers["copilot"].documentation_url


def test_config_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "omnicli.yaml"
    write_example_config(config_path)
    loaded = load_config(config_path)
    assert loaded.pipeline.stages[-1].name == "master-proposal"
    assert loaded.providers["gemini"].command == "gemini"


def test_default_provider_sources_are_registered() -> None:
    sources = (Path(__file__).parents[1] / "docs" / "provider-sources.txt").read_text(encoding="utf-8")
    for provider in DEFAULT_CONFIG.providers.values():
        assert provider.documentation_url
        assert provider.installation_url
        assert provider.documentation_url in sources
        assert provider.installation_url in sources


def test_missing_config_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        load_config(tmp_path / "missing.yaml")


def test_unknown_stage_provider_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown providers"):
        OmniConfig(
            pipeline=PipelineConfig(
                stages=[StageConfig(name="review", provider="missing", role="Reviewer", instruction="Review")]
            ),
            providers={"known": ProviderConfig(command="known")},
        )
