from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from omnicli.models import RunManifest, StageResult


def safe_run_id() -> str:
    return datetime.now(timezone.utc).strftime("run-%Y%m%d-%H%M%S-%f")[:-3]


class Workspace:
    def __init__(self, root: Path, run_id: str | None = None) -> None:
        self.root = root
        self.run_id = run_id or safe_run_id()
        self.path = self.root / self.run_id
        self.path.mkdir(parents=True, exist_ok=True)

    @property
    def manifest_path(self) -> Path:
        return self.path / "manifest.json"

    def write_text(self, name: str, content: str) -> Path:
        safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-")
        target = self.path / safe_name
        target.write_text(content, encoding="utf-8")
        return target

    def save_manifest(self, manifest: RunManifest) -> None:
        manifest.updated_at = datetime.now(timezone.utc)
        self.manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def load_manifest(self) -> RunManifest:
        return RunManifest.model_validate_json(self.manifest_path.read_text(encoding="utf-8"))

    def read_text(self, name: str) -> str:
        return (self.path / name).read_text(encoding="utf-8")

    def add_result(self, manifest: RunManifest, result: StageResult) -> None:
        manifest.stages.append(result)
        self.save_manifest(manifest)
