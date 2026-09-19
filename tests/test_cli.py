import json
import sys
from pathlib import Path

import yaml
from typer.testing import CliRunner

from omnicli.cli import app
from omnicli.models import OmniConfig, PipelineConfig, ProviderConfig, StageConfig


def test_doctor_json_is_automation_friendly(tmp_path: Path) -> None:
    config = OmniConfig(
        pipeline=PipelineConfig(
            stages=[StageConfig(name="review", provider="python", role="Reviewer", instruction="Review")]
        ),
        providers={
            "python": ProviderConfig(
                command=sys.executable,
                args=["-c", "print('ok')", "{prompt}"],
            )
        },
    )
    config_path = tmp_path / "omnicli.yaml"
    config_path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )

    result = CliRunner().invoke(app, ["doctor", "--config", str(config_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ready"] is True
    assert payload["providers"][0]["transport"] == "argv"
    assert payload["providers"][0]["capability_status"] is None
