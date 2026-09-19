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
    assert workspace.load_manifest().stages[0].prompt_sha256
    assert workspace.load_manifest().stages[0].output_sha256
    assert workspace.load_manifest().total_loops == 1
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
    assert all(result.loop == 1 for result in workspace.load_manifest().stages)


class RefiningFakeAdapter(ProviderAdapter):
    def __init__(self, name: str) -> None:
        self.provider_name = name
        self.calls = 0

    def check(self) -> str:
        return "fake 1.0"

    def run(self, prompt: str, timeout_seconds: float) -> ProviderResponse:
        self.calls += 1
        if "como: Editor técnico" in prompt and "ciclo 1" in prompt:
            output = "# Escopo\nProblema ainda não consolidado."
        else:
            output = "# Scope\n# Risks\n# Acceptance criteria\n# Pending decisions\n" + ("detail " * 30)
        return ProviderResponse(stdout=output, stderr="", exit_code=0)


def test_refinement_routes_to_targeted_suffix_and_stops_at_quality_threshold(tmp_path: Path) -> None:
    adapters = {name: RefiningFakeAdapter(name) for name in DEFAULT_CONFIG.providers}
    runner = PipelineRunner(DEFAULT_CONFIG, adapters)
    output, workspace, report = runner.run(
        "Aplicativo de meditação",
        loops=3,
        refine=True,
        output=tmp_path / "proposal.md",
        workspace_root=tmp_path / "workspace",
    )

    manifest = workspace.load_manifest()
    assert output.exists()
    assert report.score == 80
    assert manifest.execution_mode == "refinement"
    assert manifest.termination_reason.value == "quality_threshold"
    assert manifest.quality_history == [20, 80]
    assert manifest.passes_completed == 2
    assert manifest.steps_used == 9
    assert "loop-2:route:critical-review" in manifest.route_history
    assert [result.loop for result in manifest.stages] == [1, 1, 1, 1, 1, 2, 2, 2, 2]


def test_refinement_can_be_enabled_in_pipeline_config(tmp_path: Path) -> None:
    config = DEFAULT_CONFIG.model_copy(deep=True)
    config.pipeline.quality_loop.enabled = True
    adapters = {name: FakeAdapter(name) for name in config.providers}
    runner = PipelineRunner(config, adapters)
    _, workspace, report = runner.run(
        "Aplicativo de meditação",
        loops=2,
        output=tmp_path / "proposal.md",
        workspace_root=tmp_path / "workspace",
    )

    manifest = workspace.load_manifest()
    assert report.score == 80
    assert manifest.execution_mode == "refinement"
    assert manifest.termination_reason.value == "quality_threshold"
    assert manifest.steps_used == len(config.pipeline.stages)
