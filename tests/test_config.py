from pathlib import Path

import pytest

from omnicli.config import DEFAULT_CONFIG, load_config, write_example_config
from omnicli.exceptions import ConfigurationError


def test_default_config_has_critical_pipeline() -> None:
    names = [stage.name for stage in DEFAULT_CONFIG.pipeline.stages]
    assert names == [
        "discovery",
        "critical-review",
        "architecture",
        "feasibility",
        "master-proposal",
    ]


def test_config_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "omnicli.yaml"
    write_example_config(config_path)
    loaded = load_config(config_path)
    assert loaded.pipeline.stages[-1].name == "master-proposal"
    assert loaded.providers["gemini"].command == "gemini"


def test_missing_config_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        load_config(tmp_path / "missing.yaml")
