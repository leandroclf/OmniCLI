from pathlib import Path

from omnicli.adapters.base import ProviderAdapter, ProviderResponse
from omnicli.config import DEFAULT_CONFIG
from omnicli.models import StageStatus
from omnicli.pipeline import PipelineRunner


class FakeAdapter(ProviderAdapter):
    def __init__(self, name: str) -> None:
        self.provider_name = name
        self.calls = 0

    def check(self) -> str:
        return "fake 1.0"

    def run(self, prompt: str, timeout_seconds: float) -> ProviderResponse:
        self.calls += 1
        return ProviderResponse(
            stdout=(
                f"# Proposta\n\nEscopo, riscos, critérios e decisões pendentes. Etapa executada: {self.provider_name}."
            ),
            stderr="",
            exit_code=0,
        )


def test_pipeline_creates_final_document_and_artifacts(tmp_path: Path) -> None:
    adapters = {name: FakeAdapter(name) for name in DEFAULT_CONFIG.providers}
    runner = PipelineRunner(DEFAULT_CONFIG, adapters)
    output, workspace, report = runner.run(
        "Aplicativo de meditação",
        loops=1,
        output=tmp_path / "proposal.md",
        workspace_root=tmp_path / "workspace",
    )
    assert output.exists()
    assert workspace.manifest_path.exists()
    assert len(workspace.load_manifest().stages) == len(DEFAULT_CONFIG.pipeline.stages)
    assert report.score >= 50


def test_pipeline_resume_retries_failed_stage(tmp_path: Path) -> None:
    adapters = {name: FakeAdapter(name) for name in DEFAULT_CONFIG.providers}
    runner = PipelineRunner(DEFAULT_CONFIG, adapters)
    output, workspace, _ = runner.run(
        "Aplicativo de meditação",
        loops=1,
        output=tmp_path / "proposal.md",
        workspace_root=tmp_path / "workspace",
    )
    manifest = workspace.load_manifest()
    manifest.status = StageStatus.FAILED
    manifest.stages[-1].status = StageStatus.FAILED
    workspace.save_manifest(manifest)
    resumed_output, _, report = runner.resume(
        workspace.run_id,
        output=output,
        workspace_root=tmp_path / "workspace",
    )
    assert resumed_output == output
    assert report.passed
    assert workspace.load_manifest().status.value == "completed"
