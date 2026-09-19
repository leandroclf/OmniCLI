from pathlib import Path

import pytest

from omnicli.exceptions import WorkspaceError
from omnicli.models import RunManifest, StageStatus
from omnicli.workspace import Workspace


def test_workspace_writes_and_loads_manifest(tmp_path: Path) -> None:
    workspace = Workspace(tmp_path, run_id="run-test")
    manifest = RunManifest(run_id="run-test", input_file="input.md", status=StageStatus.RUNNING)
    workspace.save_manifest(manifest)
    workspace.write_text("input.md", "ideia")
    loaded = workspace.load_manifest()
    assert loaded.run_id == "run-test"
    assert loaded.status == StageStatus.RUNNING


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
