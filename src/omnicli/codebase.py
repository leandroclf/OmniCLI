"""Bounded, read-only evidence from a local folder or an HTTPS Git repository."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from omnicli.exceptions import PipelineError

MAX_FILES = 24
MAX_CANDIDATES = 5000
MAX_FILE_BYTES = 128_000
MAX_EXCERPT_CHARS = 900
MAX_CONTEXT_CHARS = 24_000
MAX_SCANNED_FILES = 240
MAX_SCANNED_BYTES = 10_000_000
EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "node_modules", "vendor", "dist", "build", "target", "coverage",
    "__pycache__", ".next", ".omnicli_workspace", "artifacts", ".terraform",
}
SENSITIVE_NAMES = {".env", ".npmrc", ".pypirc", "id_rsa", "id_ed25519", "credentials", "secrets.json"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks", ".sqlite", ".db"}
TEXT_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".kt", ".md",
    ".toml", ".yaml", ".yml", ".json", ".xml", ".sql", ".sh", ".properties",
}
KEY_FILES = {"readme.md", "pyproject.toml", "package.json", "pom.xml", "build.gradle", "go.mod"}
SECRET_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|secret|password|access[_-]?token|private[_-]?key)\s*[:=]\s*"
    r"['\"]?(?!\$|\{|<|example|changeme|your[_-])[^\s,'\"}]{8,}"
    r"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
)


@dataclass(frozen=True)
class EvidenceFile:
    path: str
    sha256: str
    excerpt: str
    truncated: bool

    def as_dict(self) -> dict[str, str | bool]:
        return {"path": self.path, "sha256": self.sha256, "excerpt": self.excerpt, "truncated": self.truncated}


@dataclass(frozen=True)
class CodebaseContext:
    source_kind: str
    commit: str | None
    dirty: bool | None
    files: tuple[EvidenceFile, ...]
    skipped: int
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        return {
            "source_kind": self.source_kind, "commit": self.commit, "dirty": self.dirty,
            "fingerprint": self.fingerprint, "skipped": self.skipped,
            "files": [item.as_dict() for item in self.files],
            "warning": "Trechos selecionados; não representa uma auditoria completa do projeto.",
        }

    def prompt_text(self) -> str:
        header = (
            f"Tipo: {self.source_kind}; commit: {self.commit or 'não disponível'}; "
            f"alterações locais: {self.dirty}\n"
        )
        items = [f"Arquivo: {item.path} | sha256: {item.sha256} | trecho parcial: {item.truncated}\n{item.excerpt}"
                 for item in self.files]
        return header + "\n\n".join(items)


def _git(*args: str, cwd: Path | None = None, timeout: int = 30) -> bytes:
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, timeout=timeout, check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PipelineError(f"Falha ao ler Git: {exc}") from exc
    if result.returncode != 0:
        raise PipelineError(f"Git não concluiu a leitura solicitada (código {result.returncode})")
    return result.stdout


def _allowed(path: str) -> bool:
    pure = PurePosixPath(path)
    parts = tuple(part.casefold() for part in pure.parts)
    name = parts[-1]
    return bool(parts) and not any(part in EXCLUDED_PARTS or part.startswith(".env") for part in parts) and (
        name in KEY_FILES or pure.suffix.casefold() in TEXT_SUFFIXES
    ) and name not in SENSITIVE_NAMES and pure.suffix.casefold() not in SENSITIVE_SUFFIXES


def _priority(path: str, terms: set[str]) -> tuple[int, str]:
    lower = path.casefold()
    score = sum(5 for term in terms if term in lower)
    if lower.startswith(("src/", "app/", "lib/")):
        score += 5
    if lower.startswith("docs/"):
        score += 1
    if PurePosixPath(path).name.casefold() in KEY_FILES:
        score += 2
    if lower.startswith(("test", "spec")):
        score += 1
    return (-score, path)


def _assemble(
    source_kind: str, commit: str | None, dirty: bool | None, idea: str,
    candidates: Sequence[tuple[str, int, object]], reader: Callable[[object], bytes],
) -> CodebaseContext:
    terms = {term.casefold() for term in re.findall(r"[\w-]{4,}", idea) if len(term) >= 4}
    ranked = sorted((item for item in candidates if _allowed(item[0])), key=lambda x: _priority(x[0], terms))
    selected: list[EvidenceFile] = []
    skipped = len(candidates) - len(ranked)
    remaining = MAX_CONTEXT_CHARS
    inspected: list[tuple[int, str, bytes, str]] = []
    scanned_bytes = 0
    for path, size, identifier in ranked:
        if len(inspected) >= MAX_SCANNED_FILES or scanned_bytes + size > MAX_SCANNED_BYTES:
            skipped += 1
            continue
        if size > MAX_FILE_BYTES:
            skipped += 1
            continue
        data = reader(identifier)
        scanned_bytes += len(data)
        if len(data) > MAX_FILE_BYTES or b"\x00" in data:
            skipped += 1
            continue
        content = data.decode("utf-8", errors="replace")
        if "\ufffd" in content or SECRET_PATTERN.search(content):
            skipped += 1
            continue
        score = -_priority(path, terms)[0]
        score += sum(4 for term in terms if term in content.casefold())
        inspected.append((score, path, data, content))
    for _score, path, data, content in sorted(inspected, key=lambda entry: (-entry[0], entry[1])):
        if len(selected) >= MAX_FILES or remaining < 200:
            skipped += 1
            continue
        matches = [content.casefold().find(term) for term in terms if term in content.casefold()]
        offset = min(matches) if matches else 0
        start = content.rfind("\n", 0, offset) + 1 if offset else 0
        line = content.count("\n", 0, start) + 1
        excerpt = content[start:start + min(MAX_EXCERPT_CHARS, remaining)].strip()
        if not excerpt:
            skipped += 1
            continue
        selected.append(EvidenceFile(
            path, hashlib.sha256(data).hexdigest(), f"L{line}: {excerpt}", start > 0 or len(content) > len(excerpt)
        ))
        remaining -= len(excerpt) + len(path) + 130
    if not selected:
        raise PipelineError("Nenhum arquivo de texto elegível foi encontrado no projeto")
    provenance = "\n".join(f"{f.path}\0{f.sha256}\0{f.excerpt}" for f in selected)
    fingerprint = hashlib.sha256(f"{source_kind}\0{commit}\0{dirty}\0{provenance}".encode()).hexdigest()
    return CodebaseContext(source_kind, commit, dirty, tuple(selected), skipped, fingerprint)


def inspect_local(root: Path, idea: str) -> CodebaseContext:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise PipelineError(f"Projeto não é uma pasta: {root}")
    git_dir = root / ".git"
    commit: str | None = None
    dirty: bool | None = None
    if git_dir.exists():
        commit = _git("rev-parse", "HEAD", cwd=root).decode().strip()
        dirty = bool(_git("status", "--porcelain", "--untracked-files=normal", cwd=root))
        names = _git("ls-files", "--cached", "--others", "--exclude-standard", "-z", cwd=root).split(b"\0")
        paths = sorted({os.fsdecode(name) for name in names if name})
    else:
        paths = []
        for base, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(
                d for d in dirs if d.casefold() not in EXCLUDED_PARTS and not (Path(base) / d).is_symlink()
            )
            paths.extend((Path(base) / name).relative_to(root).as_posix() for name in sorted(files))
            if len(paths) > MAX_CANDIDATES:
                raise PipelineError("Projeto excede o limite de 5000 arquivos inspecionáveis")
    if len(paths) > MAX_CANDIDATES:
        raise PipelineError("Projeto excede o limite de 5000 arquivos inspecionáveis")
    candidates = []
    for path in paths:
        target = root / path
        if (not _allowed(path) or target.is_symlink() or not target.resolve().is_relative_to(root)
                or not target.is_file()):
            continue
        candidates.append((path, target.stat().st_size, target))
    def read_local(identifier: object) -> bytes:
        assert isinstance(identifier, Path)
        return identifier.read_bytes()

    return _assemble("local", commit, dirty, idea, candidates, read_local)


def inspect_remote(url: str, ref: str | None, idea: str) -> CodebaseContext:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment):
        raise PipelineError("--repo exige URL HTTPS sem credenciais, query ou fragmento")
    if ref and (ref.startswith("-") or not re.fullmatch(r"[A-Za-z0-9._/-]{1,120}", ref)):
        raise PipelineError("--ref deve identificar uma branch ou tag válida")
    with tempfile.TemporaryDirectory(prefix="omnicli-codebase-") as location:
        root = Path(location) / "repository"
        clone = [
            "-c", "protocol.file.allow=never", "-c", "credential.helper=",
            "clone", "--no-checkout", "--depth", "1", "--single-branch",
        ]
        if ref:
            clone.extend(["--branch", ref])
        _git(*clone, url, str(root), timeout=120)
        commit = _git("rev-parse", "HEAD", cwd=root).decode().strip()
        entries = _git("ls-tree", "-r", "-l", "-z", "HEAD", cwd=root).split(b"\0")
        if len(entries) > MAX_CANDIDATES + 1:
            raise PipelineError("Repositório excede o limite de 5000 arquivos inspecionáveis")
        candidates = []
        for entry in entries:
            if not entry:
                continue
            metadata, raw_path = entry.split(b"\t", 1)
            mode, kind, sha, size = metadata.decode("ascii").split(" ")
            path = os.fsdecode(raw_path)
            if mode != "100644" and mode != "100755":
                continue
            if kind == "blob" and size.isdigit() and _allowed(path):
                candidates.append((path, int(size), sha))
        def read_blob(identifier: object) -> bytes:
            assert isinstance(identifier, str)
            return _git("cat-file", "blob", identifier, cwd=root)

        return _assemble("remote", commit, False, idea, candidates, read_blob)
