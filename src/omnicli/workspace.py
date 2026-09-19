from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
import tempfile
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from omnicli.exceptions import WorkspaceError
from omnicli.models import RunManifest, StageResult

MANIFEST_SCHEMA_VERSION = 1


def safe_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"run-{timestamp}-{uuid4().hex[:12]}"


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


class Workspace:
    def __init__(self, root: Path, run_id: str | None = None) -> None:
        self.root = root.expanduser().resolve()
        self.run_id = run_id or safe_run_id()
        if not RUN_ID_PATTERN.fullmatch(self.run_id) or self.run_id in {".", ".."}:
            raise ValueError("run_id inválido; use apenas letras, números, ponto, hífen e sublinhado")
        self.path = (self.root / self.run_id).resolve()
        if not self.path.is_relative_to(self.root):
            raise ValueError("run_id deve permanecer dentro do diretório de workspace")
        self.path.mkdir(parents=True, exist_ok=True)
        self.path.chmod(0o700)

    @property
    def manifest_path(self) -> Path:
        return self.path / "manifest.json"

    @property
    def lock_path(self) -> Path:
        return self.path / ".run.lock"

    @contextlib.contextmanager
    def lock(self) -> Iterator[None]:
        """Serialize writers while allowing readers to inspect a run."""
        handle = self.lock_path.open("a+", encoding="utf-8")
        try:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise WorkspaceError(f"A execução {self.run_id} já está em uso") from exc
            handle.seek(0)
            handle.truncate()
            handle.write(f"pid={os.getpid()}\n")
            handle.flush()
            os.fchmod(handle.fileno(), 0o600)
            yield
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def _safe_child(self, name: str) -> Path:
        candidate = Path(name)
        if candidate.is_absolute():
            raise ValueError("artefato deve ser um caminho relativo ao workspace")
        target = (self.path / candidate).resolve()
        if not target.is_relative_to(self.path):
            raise ValueError("artefato fora do workspace")
        return target

    def write_text(self, name: str, content: str) -> Path:
        safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-")
        if not safe_name:
            raise ValueError("nome de artefato vazio")
        target = self._safe_child(safe_name)
        with self.lock():
            self._atomic_child_write(target, content)
        return target

    @staticmethod
    def _atomic_child_write(target: Path, content: str) -> None:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.chmod(temporary_name, 0o600)
            os.replace(temporary_name, target)
        except Exception:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary_name)
            raise

    def save_manifest(self, manifest: RunManifest) -> None:
        now = datetime.now(timezone.utc)
        manifest.updated_at = now
        manifest.refresh_metrics(now)
        payload = json.dumps(manifest.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"
        with self.lock():
            fd, temporary_name = tempfile.mkstemp(prefix=".manifest-", suffix=".tmp", dir=self.path)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as temporary:
                    temporary.write(payload)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                os.chmod(temporary_name, 0o600)
                os.replace(temporary_name, self.manifest_path)
            except Exception:
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(temporary_name)
                raise

    def load_manifest(self) -> RunManifest:
        try:
            payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkspaceError(f"Manifesto inválido ou ilegível para a execução {self.run_id}") from exc
        schema_version = payload.get("schema_version", 1)
        if schema_version > MANIFEST_SCHEMA_VERSION:
            raise WorkspaceError(
                f"Manifesto schema_version={schema_version} não é suportado; "
                f"máximo suportado={MANIFEST_SCHEMA_VERSION}"
            )
        payload.setdefault("schema_version", 1)
        try:
            return RunManifest.model_validate(payload)
        except ValueError as exc:
            raise WorkspaceError(f"Manifesto inválido para a execução {self.run_id}: {exc}") from exc

    def read_text(self, name: str) -> str:
        return self._safe_child(name).read_text(encoding="utf-8")

    @staticmethod
    def write_atomic(path: Path, content: str) -> None:
        """Write a user-selected output without exposing a partial document."""
        path = path.expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temporary:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.chmod(temporary_name, 0o600)
            os.replace(temporary_name, path)
        except Exception:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary_name)
            raise

    def add_result(self, manifest: RunManifest, result: StageResult) -> None:
        manifest.stages.append(result)
        self.save_manifest(manifest)
