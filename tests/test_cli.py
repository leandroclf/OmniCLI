import json
import sys
from pathlib import Path

import yaml
from typer.testing import CliRunner

from omnicli.cli import app
from omnicli.models import OmniConfig, PipelineConfig, ProviderConfig, RunManifest, StageConfig, StageStatus
from omnicli.workspace import Workspace


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


def test_providers_check_returns_nonzero_when_required_provider_is_missing(tmp_path: Path) -> None:
    config = OmniConfig(
        pipeline=PipelineConfig(
            stages=[StageConfig(name="review", provider="missing", role="Reviewer", instruction="Review")]
        ),
        providers={"missing": ProviderConfig(command="definitely-not-installed")},
    )
    config_path = tmp_path / "omnicli.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")

    result = CliRunner().invoke(app, ["providers", "check", "--config", str(config_path)])

    assert result.exit_code == 1


def test_doctor_offline_does_not_require_provider_executables(tmp_path: Path) -> None:
    config = OmniConfig(
        pipeline=PipelineConfig(
            stages=[StageConfig(name="review", provider="missing", role="Reviewer", instruction="Review")]
        ),
        providers={"missing": ProviderConfig(command="definitely-not-installed")},
    )
    config_path = tmp_path / "omnicli.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")

    result = CliRunner().invoke(app, ["doctor", "--offline", "--json", "--config", str(config_path)])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "offline"
    assert payload["ready"] is True
    assert payload["providers"][0]["status"] == "not_checked"


def test_conceive_dry_run_is_provider_free() -> None:
    result = CliRunner().invoke(app, ["conceive", "Uma ideia", "--dry-run", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_free"] is True
    assert payload["human_review_required"] is True
    assert payload["stages"][-1] == "master-proposal"


def test_lab_commands_pass_without_authenticated_clis() -> None:
    provider_result = CliRunner().invoke(app, ["lab", "providers", "--json"])
    evaluation_result = CliRunner().invoke(app, ["lab", "evaluate", "--json"])

    assert provider_result.exit_code == 0
    assert json.loads(provider_result.stdout)["passed"] is True
    assert evaluation_result.exit_code == 0
    assert json.loads(evaluation_result.stdout)["passed"] is True


def test_run_inspect_json_returns_versioned_manifest(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path / "workspace", run_id="run-inspect")
    workspace.save_manifest(RunManifest(run_id="run-inspect", status=StageStatus.RUNNING))

    result = CliRunner().invoke(
        app,
        ["run", "inspect", "run-inspect", "--workspace", str(tmp_path / "workspace"), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1
    assert payload["workspace"].endswith("run-inspect")
