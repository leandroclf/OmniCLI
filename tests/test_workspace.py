from pathlib import Path

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
