from __future__ import annotations

import hashlib
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from omnicli.adapters.base import ProviderAdapter
from omnicli.config import config_fingerprint, config_snapshot
from omnicli.exceptions import PipelineError, ProviderError
from omnicli.models import (
    OmniConfig,
    QualityLoopConfig,
    RunManifest,
    StageResult,
    StageStatus,
    TerminationReason,
)
from omnicli.prompts import build_stage_prompt
from omnicli.quality import QualityReport, assess_document
from omnicli.workspace import Workspace

LogFn = Callable[[str], None]


@dataclass(frozen=True)
class RefinementSettings:
    enabled: bool
    min_score: int
    min_improvement: int
    stable_passes: int
    max_steps: int
    max_calls: int
    stop_on_quality: bool

    @classmethod
    def from_config(cls, config: QualityLoopConfig, enabled: bool | None = None) -> RefinementSettings:
        return cls(
            enabled=config.enabled if enabled is None else enabled,
            min_score=config.min_score,
            min_improvement=config.min_improvement,
            stable_passes=config.stable_passes,
            max_steps=config.max_steps,
            max_calls=config.max_calls,
            stop_on_quality=config.stop_on_quality,
        )


class PipelineRunner:
    def __init__(
        self,
        config: OmniConfig,
        adapters: Mapping[str, ProviderAdapter],
        logger: LogFn | None = None,
    ) -> None:
        self.config = config
        self.adapters = adapters
        self.log = logger or (lambda _message: None)

    def _adapter(self, provider: str) -> ProviderAdapter:
        try:
            return self.adapters[provider]
        except KeyError as exc:
            raise PipelineError(f"Nenhum adaptador configurado para o provedor: {provider}") from exc

    def _run_stage(
        self,
        workspace: Workspace,
        manifest: RunManifest,
        stage_index: int,
        loop: int,
        idea: str,
        previous_output: str,
        total_loops: int,
        max_calls: int | None = None,
    ) -> str:
        stage = self.config.pipeline.stages[stage_index]
        adapter = self._adapter(stage.provider)
        prompt = build_stage_prompt(stage, idea, previous_output, loop, total_loops)
        prompt_path = workspace.write_text(
            f"{loop:02d}-{stage_index + 1:02d}-{stage.name}.prompt.md",
            prompt if self.config.pipeline.retain_prompt_content else "[prompt content disabled by configuration]\n",
        )
        result = StageResult(
            stage=stage.name,
            provider=stage.provider,
            role=stage.role,
            status=StageStatus.RUNNING,
            loop=loop,
            prompt_file=str(prompt_path.relative_to(workspace.path)),
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            prompt_chars=len(prompt),
            context_chars=len(prompt),
        )
        self.log(f"loop={loop} stage={stage.name} provider={stage.provider}")
        last_error: str | None = None
        for attempt in range(stage.max_retries + 1):
            try:
                provider_version = adapter.check()
                if max_calls is not None and manifest.calls_used >= max_calls:
                    raise PipelineError(
                        f"Limite de chamadas atingido: max_calls={max_calls}; etapa pendente={stage.name}"
                    )
                manifest.calls_used += 1
                started = time.perf_counter()
                response = adapter.run(prompt, stage.timeout_seconds)
                result.attempts = attempt + 1
                result.duration_ms = int((time.perf_counter() - started) * 1000)
                if response.exit_code != 0:
                    detail = response.stderr.strip()[-1000:]
                    raise ProviderError(
                        f"{stage.provider} terminou com código {response.exit_code}" + (f": {detail}" if detail else "")
                    )
                output = response.stdout.strip()
                if not output:
                    raise ProviderError(f"{stage.provider} retornou uma saída vazia")
                output_path = workspace.write_text(f"{loop:02d}-{stage_index + 1:02d}-{stage.name}.md", output + "\n")
                result.status = StageStatus.COMPLETED
                result.finished_at = datetime.now(timezone.utc)
                result.exit_code = response.exit_code
                result.output_file = str(output_path.relative_to(workspace.path))
                result.provider_version = provider_version
                result.output_chars = len(output)
                result.output_sha256 = hashlib.sha256(output.encode("utf-8")).hexdigest()
                workspace.add_result(manifest, result)
                return output
            except ProviderError as exc:
                last_error = str(exc)
                result.attempts = attempt + 1
                self.log(f"tentativa={attempt + 1} falhou: {last_error}")
                if attempt < stage.max_retries:
                    time.sleep(min(2**attempt, 8))
        result.status = StageStatus.FAILED
        result.finished_at = datetime.now(timezone.utc)
        result.error = last_error or "erro desconhecido"
        workspace.add_result(manifest, result)
        raise PipelineError(f"Etapa {stage.name} falhou: {result.error}")

    def _record_quality(
        self,
        workspace: Workspace,
        manifest: RunManifest,
        report: QualityReport,
        output: str,
    ) -> tuple[str, int]:
        previous_score = manifest.quality_score
        delta = report.score - previous_score if previous_score is not None else report.score
        manifest.quality_score = report.score
        manifest.quality_delta = delta
        manifest.quality_history.append(report.score)
        manifest.quality_warnings = list(report.warnings)
        manifest.quality_missing_concepts = list(report.missing_concepts)
        manifest.quality_security_violations = list(report.security_violations)
        manifest.quality_critical_contradictions = list(report.critical_contradictions)
        manifest.quality_evidence = list(report.evidence)
        manifest.quality_evaluation_version = report.evaluation_version
        last_result = manifest.stages[-1] if manifest.stages else None
        output_file = last_result.output_file if last_result else None
        if manifest.best_quality_score is None or report.score >= manifest.best_quality_score:
            manifest.best_quality_score = report.score
            manifest.best_output_file = output_file
            best_output = output
        elif manifest.best_output_file:
            best_output = workspace.read_text(manifest.best_output_file)
        else:
            best_output = output
        return best_output, delta

    def _write_final(
        self,
        workspace: Workspace,
        manifest: RunManifest,
        content: str,
        output: Path | None,
        report: QualityReport,
    ) -> tuple[Path, Workspace, QualityReport]:
        if not content.strip():
            raise PipelineError("O pipeline terminou sem produzir uma proposta")
        final_path = output or Path(manifest.output_target or self.config.pipeline.output)
        Workspace.write_atomic(final_path, content.rstrip() + "\n")
        manifest.final_output = str(final_path)
        manifest.quality_score = report.score
        manifest.quality_warnings = list(report.warnings)
        manifest.quality_missing_concepts = list(report.missing_concepts)
        manifest.quality_security_violations = list(report.security_violations)
        manifest.quality_critical_contradictions = list(report.critical_contradictions)
        manifest.quality_evidence = list(report.evidence)
        manifest.quality_evaluation_version = report.evaluation_version
        manifest.current_stage = None
        manifest.next_stage = None
        manifest.status = StageStatus.COMPLETED
        workspace.save_manifest(manifest)
        return final_path, workspace, report

    def _run_refinement(
        self,
        workspace: Workspace,
        manifest: RunManifest,
        idea: str,
        settings: RefinementSettings,
        start_loop: int = 1,
        start_index: int = 0,
        previous: str = "",
        best_output: str = "",
    ) -> tuple[str, QualityReport]:
        stage_indexes = {stage.name: index for index, stage in enumerate(self.config.pipeline.stages)}
        if not best_output and manifest.best_output_file:
            best_output = workspace.read_text(manifest.best_output_file)
        if not best_output:
            best_output = previous

        stable_count = 0
        loop = start_loop
        stage_index = start_index
        while loop <= manifest.total_loops:
            manifest.current_loop = loop
            while stage_index < len(self.config.pipeline.stages):
                if manifest.steps_used >= settings.max_steps:
                    if not manifest.best_output_file:
                        raise PipelineError("max_steps foi atingido antes de produzir uma Proposta Mestra")
                    manifest.termination_reason = TerminationReason.MAX_STEPS
                    return best_output, assess_document(best_output)
                if manifest.calls_used >= settings.max_calls:
                    if not manifest.best_output_file:
                        raise PipelineError("max_calls foi atingido antes de produzir uma Proposta Mestra")
                    manifest.termination_reason = TerminationReason.MAX_CALLS
                    return best_output, assess_document(best_output)

                stage = self.config.pipeline.stages[stage_index]
                manifest.current_stage = stage.name
                manifest.next_stage = stage.name
                manifest.route_history.append(f"loop-{loop}:{stage.name}")
                workspace.save_manifest(manifest)
                previous = self._run_stage(
                    workspace,
                    manifest,
                    stage_index,
                    loop,
                    idea,
                    previous,
                    manifest.total_loops,
                    settings.max_calls,
                )
                manifest.steps_used += 1
                stage_index += 1

            report = assess_document(previous)
            best_output, delta = self._record_quality(workspace, manifest, report, previous)
            manifest.passes_completed = max(manifest.passes_completed, loop)
            manifest.current_stage = None
            workspace.save_manifest(manifest)

            if settings.stop_on_quality and report.gate_passed(settings.min_score):
                manifest.termination_reason = TerminationReason.QUALITY_THRESHOLD
                return best_output, assess_document(best_output)

            if report.hard_gates_passed and len(manifest.quality_history) > 1:
                if delta < settings.min_improvement:
                    stable_count += 1
                else:
                    stable_count = 0
                if stable_count >= settings.stable_passes:
                    manifest.termination_reason = TerminationReason.STABLE_RESULT
                    return best_output, assess_document(best_output)

            if loop >= manifest.total_loops:
                manifest.termination_reason = (
                    TerminationReason.QUALITY_GATE_BLOCKED
                    if not report.hard_gates_passed
                    else TerminationReason.MAX_PASSES
                )
                return best_output, assess_document(best_output)

            target_name = report.recommended_stage or "critical-review"
            stage_index = stage_indexes.get(target_name, 0)
            loop += 1
            manifest.route_history.append(f"loop-{loop}:route:{self.config.pipeline.stages[stage_index].name}")
            manifest.next_stage = self.config.pipeline.stages[stage_index].name
            workspace.save_manifest(manifest)

        manifest.termination_reason = TerminationReason.MAX_PASSES
        return best_output, assess_document(best_output)

    def run(
        self,
        idea: str,
        loops: int,
        output: Path | None = None,
        workspace_root: Path | None = None,
        run_id: str | None = None,
        refine: bool | None = None,
    ) -> tuple[Path, Workspace, QualityReport]:
        if not idea.strip():
            raise PipelineError("A ideia inicial não pode ser vazia")
        if loops < 1 or loops > self.config.pipeline.max_loops:
            raise PipelineError(f"--loops deve estar entre 1 e {self.config.pipeline.max_loops}")
        settings = RefinementSettings.from_config(self.config.pipeline.quality_loop, enabled=refine)
        workspace = Workspace(workspace_root or self.config.pipeline.workspace, run_id=run_id)
        if run_id and workspace.manifest_path.exists():
            raise PipelineError(f"A execução {run_id} já existe; use run resume para continuar")
        normalized_idea = idea.strip()
        input_sha256 = hashlib.sha256(normalized_idea.encode("utf-8")).hexdigest()
        input_path = (
            workspace.write_text("input.md", normalized_idea + "\n")
            if self.config.pipeline.input_retention.value == "local"
            else None
        )
        manifest = RunManifest(
            run_id=workspace.run_id,
            input_file=str(input_path.relative_to(workspace.path)) if input_path else None,
            input_sha256=input_sha256,
            output_target=str(output or self.config.pipeline.output),
            config_snapshot=config_snapshot(self.config),
            config_fingerprint=config_fingerprint(self.config),
            graph_version=self.config.pipeline.graph_version,
            status=StageStatus.RUNNING,
            total_loops=loops,
            execution_mode="refinement" if settings.enabled else "legacy",
        )
        workspace.save_manifest(manifest)

        previous = ""
        try:
            if settings.enabled:
                previous, report = self._run_refinement(workspace, manifest, normalized_idea, settings)
                return self._write_final(workspace, manifest, previous, output, report)

            for loop in range(1, loops + 1):
                manifest.current_loop = loop
                manifest.passes_completed = loop - 1
                for stage_index, stage in enumerate(self.config.pipeline.stages):
                    manifest.current_stage = stage.name
                    manifest.next_stage = stage.name
                    workspace.save_manifest(manifest)
                    previous = self._run_stage(
                        workspace,
                        manifest,
                        stage_index,
                        loop,
                        normalized_idea,
                        previous,
                        loops,
                        self.config.pipeline.quality_loop.max_calls,
                    )
                    manifest.steps_used += 1
                manifest.passes_completed = loop
                workspace.save_manifest(manifest)
            manifest.termination_reason = TerminationReason.COMPLETED
            return self._write_final(workspace, manifest, previous, output, assess_document(previous))
        except Exception:
            manifest.status = StageStatus.FAILED
            manifest.termination_reason = TerminationReason.FAILED
            workspace.save_manifest(manifest)
            raise

    def _resume_idea(self, workspace: Workspace, manifest: RunManifest, idea: str | None) -> str:
        if idea is not None and idea.strip():
            normalized = idea.strip()
            input_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            if manifest.input_sha256 and input_hash != manifest.input_sha256:
                raise PipelineError("A ideia informada não corresponde ao hash registrado na execução")
            return normalized
        if manifest.input_file:
            return workspace.read_text(manifest.input_file).strip()
        raise PipelineError(
            "Esta execução não reteve a ideia original; informe --idea para retomar com validação de hash"
        )

    def _resume_refinement(
        self,
        workspace: Workspace,
        manifest: RunManifest,
        output: Path | None,
        idea: str,
    ) -> tuple[Path, Workspace, QualityReport]:
        stage_indexes = {stage.name: index for index, stage in enumerate(self.config.pipeline.stages)}
        start_index = stage_indexes.get(manifest.next_stage or "")
        if start_index is None:
            raise PipelineError("Não foi possível determinar a próxima etapa do refinamento")
        previous = ""
        completed_results = [result for result in manifest.stages if result.status == StageStatus.COMPLETED]
        if completed_results and completed_results[-1].output_file:
            previous = workspace.read_text(completed_results[-1].output_file)
        best_output = workspace.read_text(manifest.best_output_file) if manifest.best_output_file else previous
        settings = RefinementSettings.from_config(self.config.pipeline.quality_loop, enabled=True)
        manifest.status = StageStatus.RUNNING
        try:
            content, report = self._run_refinement(
                workspace,
                manifest,
                idea,
                settings,
                start_loop=max(1, manifest.current_loop),
                start_index=start_index,
                previous=previous,
                best_output=best_output,
            )
            return self._write_final(workspace, manifest, content, output, report)
        except Exception:
            manifest.status = StageStatus.FAILED
            manifest.termination_reason = TerminationReason.FAILED
            workspace.save_manifest(manifest)
            raise

    def resume(
        self,
        run_id: str,
        output: Path | None = None,
        workspace_root: Path | None = None,
        idea: str | None = None,
        allow_config_change: bool = False,
    ) -> tuple[Path, Workspace, QualityReport]:
        """Resume the first incomplete stage from an existing workspace."""
        workspace = Workspace(workspace_root or self.config.pipeline.workspace, run_id=run_id)
        if not workspace.manifest_path.exists():
            raise PipelineError(f"Execução não encontrada: {run_id}")
        manifest = workspace.load_manifest()
        if manifest.config_fingerprint and not allow_config_change:
            current_fingerprint = config_fingerprint(self.config)
            if current_fingerprint != manifest.config_fingerprint:
                raise PipelineError(
                    "A configuração atual difere da configuração da execução; "
                    "use --allow-config-change apenas após revisar o impacto"
                )
        if manifest.status == StageStatus.COMPLETED:
            raise PipelineError(f"A execução {run_id} já foi concluída")
        if manifest.execution_mode == "refinement":
            return self._resume_refinement(workspace, manifest, output, self._resume_idea(workspace, manifest, idea))

        stage_indexes = {stage.name: index for index, stage in enumerate(self.config.pipeline.stages)}
        last_result = manifest.stages[-1] if manifest.stages else None
        if last_result is None:
            raise PipelineError(f"A execução {run_id} não possui etapas registradas")

        previous = ""
        completed_results = [result for result in manifest.stages if result.status == StageStatus.COMPLETED]
        if completed_results:
            previous_result = completed_results[-1]
            if previous_result.output_file:
                previous = workspace.read_text(previous_result.output_file)
        resume_idea = self._resume_idea(workspace, manifest, idea)

        if last_result.status == StageStatus.FAILED:
            start_loop = last_result.loop
            start_index = stage_indexes.get(last_result.stage)
        else:
            start_loop = last_result.loop
            start_index = stage_indexes.get(last_result.stage, -1) + 1
            if start_index >= len(self.config.pipeline.stages):
                start_loop += 1
                start_index = 0

        if start_index is None or start_loop > manifest.total_loops:
            raise PipelineError("Não foi possível determinar a próxima etapa da execução")

        manifest.status = StageStatus.RUNNING
        try:
            for loop in range(start_loop, manifest.total_loops + 1):
                manifest.current_loop = loop
                for stage_index in range(start_index if loop == start_loop else 0, len(self.config.pipeline.stages)):
                    manifest.current_stage = self.config.pipeline.stages[stage_index].name
                    manifest.next_stage = self.config.pipeline.stages[stage_index].name
                    workspace.save_manifest(manifest)
                    previous = self._run_stage(
                        workspace,
                        manifest,
                        stage_index,
                        loop,
                        resume_idea,
                        previous,
                        manifest.total_loops,
                    )
                    manifest.steps_used += 1
                manifest.passes_completed = loop
            manifest.termination_reason = TerminationReason.COMPLETED
            return self._write_final(workspace, manifest, previous, output, assess_document(previous))
        except Exception:
            manifest.status = StageStatus.FAILED
            manifest.termination_reason = TerminationReason.FAILED
            workspace.save_manifest(manifest)
            raise
