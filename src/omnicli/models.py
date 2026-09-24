from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TerminationReason(str, Enum):
    QUALITY_THRESHOLD = "quality_threshold"
    STABLE_RESULT = "stable_result"
    MAX_PASSES = "max_passes"
    MAX_STEPS = "max_steps"
    MAX_CALLS = "max_calls"
    QUALITY_GATE_BLOCKED = "quality_gate_blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class InputRetention(str, Enum):
    HASH_ONLY = "hash-only"
    LOCAL = "local"


class StageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    provider: str = Field(min_length=1, max_length=80)
    role: str = Field(min_length=1, max_length=120)
    instruction: str = Field(min_length=1)
    timeout_seconds: float = Field(default=300, gt=0, le=3600)
    max_retries: int = Field(default=1, ge=0, le=5)


class QualityLoopConfig(BaseModel):
    """Bounded, opt-in routing after a proposal quality check."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    min_score: int = Field(default=80, ge=0, le=100)
    min_improvement: int = Field(default=3, ge=0, le=100)
    stable_passes: int = Field(default=1, ge=1, le=5)
    max_steps: int = Field(default=30, ge=1, le=100)
    max_calls: int = Field(default=50, ge=1, le=500)
    stop_on_quality: bool = True


class PipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "conception"
    stages: list[StageConfig] = Field(min_length=1)
    max_loops: int = Field(default=3, ge=1, le=10)
    workspace: Path = Path(".omnicli_workspace")
    output: Path = Path("proposta.md")
    retain_prompt_content: bool = False
    input_retention: InputRetention = InputRetention.HASH_ONLY
    graph_version: str = Field(default="conception-v1", min_length=1, max_length=40)
    quality_loop: QualityLoopConfig = Field(default_factory=QualityLoopConfig)

    @field_validator("stages")
    @classmethod
    def unique_stage_names(cls, value: list[StageConfig]) -> list[StageConfig]:
        names = [stage.name for stage in value]
        if len(names) != len(set(names)):
            raise ValueError("stage names must be unique")
        return value


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)
    enabled: bool = True
    version_args: list[str] = Field(default_factory=lambda: ["--version"])
    capability_args: list[str] = Field(default_factory=lambda: ["--help"])
    required_capabilities: list[str] = Field(default_factory=list)
    documentation_url: str | None = None
    installation_url: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)
    environment_allowlist: list[str] = Field(
        default_factory=lambda: ["PATH", "HOME", "USER", "TMPDIR", "LANG", "LC_ALL"]
    )
    inherit_environment: bool = False
    max_prompt_chars: int = Field(default=200_000, ge=1_000, le=1_000_000)
    max_output_chars: int = Field(default=500_000, ge=1_000, le=5_000_000)
    max_stderr_chars: int = Field(default=20_000, ge=1_000, le=1_000_000)

    @field_validator("args")
    @classmethod
    def validate_prompt_placeholder(cls, value: list[str]) -> list[str]:
        if any("{prompt}" in argument and argument != "{prompt}" for argument in value):
            raise ValueError("{prompt} must be an isolated argument")
        placeholders = sum(argument.count("{prompt}") for argument in value)
        if placeholders > 1:
            raise ValueError("provider args may contain {prompt} at most once")
        return value


class OmniConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipeline: PipelineConfig
    providers: dict[str, ProviderConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def stages_reference_known_providers(self) -> OmniConfig:
        unknown = sorted({stage.provider for stage in self.pipeline.stages if stage.provider not in self.providers})
        if unknown:
            raise ValueError(f"pipeline references unknown providers: {', '.join(unknown)}")
        return self


class StageResult(BaseModel):
    stage: str
    provider: str
    role: str
    status: StageStatus
    loop: int
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    exit_code: int | None = None
    output_file: str | None = None
    prompt_file: str | None = None
    error: str | None = None
    provider_version: str | None = None
    output_chars: int = 0
    prompt_chars: int = 0
    context_chars: int = 0
    prompt_sha256: str | None = None
    output_sha256: str | None = None
    attempts: int = 0
    duration_ms: int | None = None


class RunMetrics(BaseModel):
    """Bounded, local metrics useful for pilot and release evaluation."""

    elapsed_ms: int = 0
    total_stage_duration_ms: int = 0
    failed_stage_count: int = 0
    retry_count: int = 0
    prompt_chars: int = 0
    output_chars: int = 0
    max_context_chars: int = 0
    context_growth_chars: int = 0


class RunManifest(BaseModel):
    schema_version: int = Field(default=1, ge=1, le=100)
    run_id: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    input_file: str | None = None
    input_sha256: str | None = None
    context_fingerprint: str | None = None
    context_source_kind: str | None = None
    context_commit: str | None = None
    context_dirty: bool | None = None
    context_files: list[dict[str, str | bool]] = Field(default_factory=list)
    final_output: str | None = None
    output_target: str | None = None
    status: StageStatus = StageStatus.PENDING
    current_loop: int = 0
    total_loops: int = Field(default=1, ge=1, le=10)
    stages: list[StageResult] = Field(default_factory=list)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
    config_fingerprint: str | None = None
    graph_version: str = "conception-v1"
    execution_mode: str = "legacy"
    current_stage: str | None = None
    next_stage: str | None = None
    steps_used: int = Field(default=0, ge=0)
    calls_used: int = Field(default=0, ge=0)
    passes_completed: int = Field(default=0, ge=0)
    quality_score: int | None = Field(default=None, ge=0, le=100)
    best_quality_score: int | None = Field(default=None, ge=0, le=100)
    quality_delta: int | None = None
    quality_history: list[int] = Field(default_factory=list)
    route_history: list[str] = Field(default_factory=list)
    quality_warnings: list[str] = Field(default_factory=list)
    quality_missing_concepts: list[str] = Field(default_factory=list)
    quality_security_violations: list[str] = Field(default_factory=list)
    quality_critical_contradictions: list[str] = Field(default_factory=list)
    quality_evidence: list[str] = Field(default_factory=list)
    quality_evaluation_version: str | None = None
    best_output_file: str | None = None
    termination_reason: TerminationReason | None = None
    metrics: RunMetrics = Field(default_factory=RunMetrics)

    def refresh_metrics(self, now: datetime | None = None) -> None:
        """Recompute metrics from the auditable stage records."""
        current = now or utc_now()
        contexts = [stage.context_chars for stage in self.stages if stage.context_chars > 0]
        first_context = contexts[0] if contexts else 0
        self.metrics = RunMetrics(
            elapsed_ms=max(0, int((current - self.created_at).total_seconds() * 1000)),
            total_stage_duration_ms=sum(stage.duration_ms or 0 for stage in self.stages),
            failed_stage_count=sum(stage.status == StageStatus.FAILED for stage in self.stages),
            retry_count=sum(max(0, stage.attempts - 1) for stage in self.stages),
            prompt_chars=sum(stage.prompt_chars for stage in self.stages),
            output_chars=sum(stage.output_chars for stage in self.stages),
            max_context_chars=max(contexts, default=0),
            context_growth_chars=max(contexts, default=0) - first_context,
        )
