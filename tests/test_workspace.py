from pathlib import Path

import pytest

from omnicli.exceptions import WorkspaceError
from omnicli.models import RunManifest, StageResult, StageStatus
from omnicli.workspace import Workspace


def test_workspace_writes_and_loads_manifest(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path, run_id="run-test")
    manifest = RunManifest(run_id="run-test", input_file="input.md", status=StageStatus.RUNNING)
    workspace.save_manifest(manifest)
    workspace.write_text("input.md", "ideia")
    loaded = workspace.load_manifest()
    assert loaded.run_id == "run-test"
    assert loaded.status == StageStatus.RUNNING
    assert loaded.schema_version == 1


def test_workspace_rejects_path_traversal_run_ids(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError):
        Workspace(tmp_path, run_id="../outside")

    with pytest.raises(ValueError):
        Workspace(tmp_path, run_id="/tmp/outside")


def test_workspace_uses_restrictive_permissions(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path, run_id="run-secure")
    manifest = RunManifest(run_id="run-secure", input_file=None, status=StageStatus.RUNNING)
    workspace.save_manifest(manifest)

    assert oct(workspace.path.stat().st_mode & 0o777) == "0o700"
    assert oct(workspace.manifest_path.stat().st_mode & 0o777) == "0o600"


def test_workspace_lock_rejects_concurrent_writer(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path, run_id="run-locked")
    other_handle = Workspace(tmp_path, run_id="run-locked")

    with workspace.lock():
        with pytest.raises(WorkspaceError, match="já está em uso"):
            with other_handle.lock():
                pass


def test_workspace_rejects_future_manifest_schema(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path, run_id="run-future")
    workspace.manifest_path.write_text('{"schema_version": 99, "run_id": "run-future"}', encoding="utf-8")

    with pytest.raises(WorkspaceError, match="schema_version=99"):
        workspace.load_manifest()


def test_manifest_metrics_are_derived_from_stage_records(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path, run_id="run-metrics")
    manifest = RunManifest(run_id="run-metrics", status=StageStatus.RUNNING)
    manifest.stages.append(
        StageResult(
            stage="review",
            provider="test",
            role="Reviewer",
            status=StageStatus.COMPLETED,
            loop=1,
            attempts=2,
            prompt_chars=10,
            context_chars=10,
            output_chars=20,
            duration_ms=5,
        )
    )
    workspace.save_manifest(manifest)

    metrics = workspace.load_manifest().metrics
    assert metrics.total_stage_duration_ms == 5
    assert metrics.retry_count == 1
    assert metrics.prompt_chars == 10
    assert metrics.output_chars == 20
    assert metrics.failed_stage_count == 0
