from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    provider: str = Field(min_length=1, max_length=80)
    role: str = Field(min_length=1, max_length=120)
    instruction: str = Field(min_length=1)
    timeout_seconds: float = Field(default=300, gt=0, le=3600)
    max_retries: int = Field(default=1, ge=0, le=5)


class PipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = "conception"
    stages: list[StageConfig] = Field(min_length=1)
    max_loops: int = Field(default=3, ge=1, le=10)
    workspace: Path = Path(".omnicli_workspace")
    output: Path = Path("proposta.md")
    retain_prompt_content: bool = False

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
    environment: dict[str, str] = Field(default_factory=dict)


class OmniConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipeline: PipelineConfig
    providers: dict[str, ProviderConfig] = Field(min_length=1)


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


class RunManifest(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    input_file: str
    final_output: str | None = None
    status: StageStatus = StageStatus.PENDING
    current_loop: int = 0
    stages: list[StageResult] = Field(default_factory=list)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
