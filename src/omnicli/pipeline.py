from __future__ import annotations

import hashlib
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path

from omnicli.adapters.base import ProviderAdapter
from omnicli.exceptions import PipelineError, ProviderError
from omnicli.models import OmniConfig, RunManifest, StageResult, StageStatus
from omnicli.prompts import build_stage_prompt
from omnicli.quality import QualityReport, assess_document
from omnicli.workspace import Workspace

LogFn = Callable[[str], None]


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
        )
        self.log(f"loop={loop} stage={stage.name} provider={stage.provider}")
        last_error: str | None = None
        for attempt in range(stage.max_retries + 1):
            try:
                provider_version = adapter.check()
                response = adapter.run(prompt, stage.timeout_seconds)
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
                self.log(f"tentativa={attempt + 1} falhou: {last_error}")
                if attempt < stage.max_retries:
                    time.sleep(min(2**attempt, 8))
        result.status = StageStatus.FAILED
        result.finished_at = datetime.now(timezone.utc)
        result.error = last_error or "erro desconhecido"
        workspace.add_result(manifest, result)
        raise PipelineError(f"Etapa {stage.name} falhou: {result.error}")

    def run(
        self,
        idea: str,
        loops: int,
        output: Path | None = None,
        workspace_root: Path | None = None,
        run_id: str | None = None,
    ) -> tuple[Path, Workspace, QualityReport]:
        if not idea.strip():
            raise PipelineError("A ideia inicial não pode ser vazia")
        if loops < 1 or loops > self.config.pipeline.max_loops:
            raise PipelineError(f"--loops deve estar entre 1 e {self.config.pipeline.max_loops}")
        workspace = Workspace(workspace_root or self.config.pipeline.workspace, run_id=run_id)
        input_path = workspace.write_text("input.md", idea.strip() + "\n")
        manifest = RunManifest(
            run_id=workspace.run_id,
            input_file=str(input_path.relative_to(workspace.path)),
            config_snapshot=self.config.model_dump(mode="json"),
            status=StageStatus.RUNNING,
            total_loops=loops,
        )
        workspace.save_manifest(manifest)

        previous = ""
        try:
            for loop in range(1, loops + 1):
                manifest.current_loop = loop
                workspace.save_manifest(manifest)
                for stage_index in range(len(self.config.pipeline.stages)):
                    previous = self._run_stage(
                        workspace,
                        manifest,
                        stage_index,
                        loop,
                        idea,
                        previous,
                        loops,
                    )
            final_path = output or self.config.pipeline.output
            final_path.parent.mkdir(parents=True, exist_ok=True)
            final_path.write_text(previous + "\n", encoding="utf-8")
            manifest.final_output = str(final_path)
            manifest.status = StageStatus.COMPLETED
            workspace.save_manifest(manifest)
            return final_path, workspace, assess_document(previous)
        except Exception:
            manifest.status = StageStatus.FAILED
            workspace.save_manifest(manifest)
            raise

    def resume(
        self,
        run_id: str,
        output: Path | None = None,
        workspace_root: Path | None = None,
    ) -> tuple[Path, Workspace, QualityReport]:
        """Resume the first incomplete stage from an existing workspace."""
        workspace = Workspace(workspace_root or self.config.pipeline.workspace, run_id=run_id)
        if not workspace.manifest_path.exists():
            raise PipelineError(f"Execução não encontrada: {run_id}")
        manifest = workspace.load_manifest()
        if manifest.status == StageStatus.COMPLETED:
            raise PipelineError(f"A execução {run_id} já foi concluída")

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
                workspace.save_manifest(manifest)
                for stage_index in range(start_index if loop == start_loop else 0, len(self.config.pipeline.stages)):
                    previous = self._run_stage(
                        workspace,
                        manifest,
                        stage_index,
                        loop,
                        workspace.read_text(manifest.input_file).strip(),
                        previous,
                        manifest.total_loops,
                    )
            final_path = output or self.config.pipeline.output
            final_path.parent.mkdir(parents=True, exist_ok=True)
            final_path.write_text(previous + "\n", encoding="utf-8")
            manifest.final_output = str(final_path)
            manifest.status = StageStatus.COMPLETED
            workspace.save_manifest(manifest)
            return final_path, workspace, assess_document(previous)
        except Exception:
            manifest.status = StageStatus.FAILED
            workspace.save_manifest(manifest)
            raise
