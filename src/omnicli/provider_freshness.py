"""Official provider CLI version checks with a small, non-sensitive cache."""

from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from omnicli.adapters.subprocess import SubprocessAdapter
from omnicli.exceptions import OmniCLIError
from omnicli.models import OmniConfig, ProviderConfig

CACHE_TTL = timedelta(hours=12)
HTTP_TIMEOUT_SECONDS = 3
MAX_METADATA_BYTES = 1_000_000
VERSION_PATTERN = re.compile(r"(?<!\d)(\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?)")


@dataclass(frozen=True)
class ProviderFreshness:
    name: str
    installed_version: str | None
    latest_version: str | None
    status: str
    checked_at: str | None
    documentation_url: str | None
    release_notes_url: str | None
    update_command_hint: str | None
    detail: str

    def as_dict(self) -> dict[str, str | None]:
        return asdict(self)


def default_cache_path() -> Path:
    cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return cache_root / "omnicli" / "provider-versions.json"


def _parse_version(value: str) -> tuple[tuple[int, int, int], int, str] | None:
    match = VERSION_PATTERN.search(value)
    if not match:
        return None
    version = match.group(1).split("+", maxsplit=1)[0]
    numeric, separator, prerelease = version.partition("-")
    parts = [int(part) for part in numeric.split(".")]
    normalized = (parts + [0, 0, 0])[:3]
    return (normalized[0], normalized[1], normalized[2]), int(not separator), prerelease


def _compare_versions(installed: str, latest: str) -> int | None:
    current_parts = _parse_version(installed)
    latest_parts = _parse_version(latest)
    if current_parts is None or latest_parts is None:
        return None
    if current_parts[:2] == latest_parts[:2]:
        if current_parts[2] == latest_parts[2]:
            return 0
        if current_parts[1] != latest_parts[1]:
            return 1 if current_parts[1] > latest_parts[1] else -1
        return (current_parts[2] > latest_parts[2]) - (current_parts[2] < latest_parts[2])
    return (current_parts[:2] > latest_parts[:2]) - (current_parts[:2] < latest_parts[:2])


def _latest_from_payload(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("metadado oficial em formato inesperado")
    raw = payload.get("version") or payload.get("tag_name")
    if not isinstance(raw, str):
        raise ValueError("metadado oficial sem versão")
    match = VERSION_PATTERN.search(raw)
    if not match:
        raise ValueError("versão ausente ou inválida no metadado oficial")
    return match.group(1)


def _http_fetch(url: str) -> tuple[str, str]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "OmniCLI-provider-freshness"},
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        raw = response.read(MAX_METADATA_BYTES + 1)
        if len(raw) > MAX_METADATA_BYTES:
            raise ValueError("metadado oficial excede 1 MB")
        payload = json.loads(raw)
    version = _latest_from_payload(payload)
    return version, datetime.now(timezone.utc).isoformat()


def _read_cache(path: Path) -> dict[str, dict[str, str]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        url: value for url, value in raw.items()
        if isinstance(url, str) and isinstance(value, dict)
        and isinstance(value.get("version"), str) and isinstance(value.get("checked_at"), str)
    }


def _write_cache(path: Path, cache: dict[str, dict[str, str]]) -> None:
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(cache, sort_keys=True, indent=2) + "\n"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
            temporary.write(serialized)
            temporary_path = Path(temporary.name)
        temporary_path.replace(path)
    except OSError:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def _cached_latest(
    url: str,
    cache: dict[str, dict[str, str]],
    now: datetime,
    fetch: Callable[[str], tuple[str, str]],
) -> tuple[str | None, str | None, str | None]:
    entry = cache.get(url)
    if entry:
        try:
            cached_datetime = datetime.fromisoformat(entry["checked_at"])
            if cached_datetime.tzinfo is None:
                cached_datetime = cached_datetime.replace(tzinfo=timezone.utc)
            if now - cached_datetime.astimezone(timezone.utc) < CACHE_TTL:
                return entry["version"], entry["checked_at"], None
        except (KeyError, ValueError):
            pass
    try:
        version, fetched_at = fetch(url)
        cache[url] = {"version": version, "checked_at": fetched_at}
        return version, fetched_at, None
    except (OSError, ValueError, urllib.error.URLError, TimeoutError) as exc:
        if entry:
            return entry["version"], entry["checked_at"], f"sem conexão; usando cache anterior: {exc}"
        return None, None, f"não foi possível consultar a fonte oficial: {exc}"


def check_provider_freshness(
    config: OmniConfig,
    providers: set[str] | None = None,
    *,
    cache_path: Path | None = None,
    now: datetime | None = None,
    fetch: Callable[[str], tuple[str, str]] = _http_fetch,
) -> tuple[ProviderFreshness, ...]:
    """Compare installed versions with official release metadata, without updates."""
    selected = providers or {stage.provider for stage in config.pipeline.stages}
    cache_file = cache_path or default_cache_path()
    cache = _read_cache(cache_file)
    original_cache = cache.copy()
    instant = now or datetime.now(timezone.utc)
    results: list[ProviderFreshness] = []

    for name in sorted(selected):
        provider: ProviderConfig | None = config.providers.get(name)
        if provider is None:
            continue
        documentation_url = provider.documentation_url
        release_notes_url = provider.release_notes_url or documentation_url
        hint = provider.update_command_hint
        installed: str | None = None
        latest: str | None = None
        checked_at: str | None = None
        source_error: str | None = None
        detail = ""
        try:
            version_output = SubprocessAdapter(name, provider).check()
            version_match = VERSION_PATTERN.search(version_output)
            installed = version_match.group(1) if version_match else None
        except (OmniCLIError, OSError) as exc:
            detail = f"não foi possível ler a versão instalada: {exc}"

        if provider.latest_version_url:
            latest, checked_at, source_error = _cached_latest(
                provider.latest_version_url, cache, instant, fetch,
            )
            if source_error:
                detail = "; ".join(part for part in (detail, source_error) if part)

        comparison = _compare_versions(installed, latest) if installed and latest else None
        if comparison is None:
            status = "unknown"
            if not detail:
                detail = "fonte de versão oficial não declarada ou versão não interpretável"
        elif comparison < 0:
            status = "update_available"
            detail = "; ".join(part for part in (f"versão oficial mais recente: {latest}", detail) if part)
        elif comparison > 0:
            status = "newer_than_registry"
            detail = "; ".join(part for part in (
                "versão instalada é posterior à versão estável publicada na fonte consultada", detail,
            ) if part)
        else:
            status = "current"
            detail = "; ".join(part for part in (
                "versão instalada corresponde à versão estável da fonte oficial", detail,
            ) if part)
        if source_error and status == "current":
            status = "unknown"
        results.append(ProviderFreshness(
            name=name,
            installed_version=installed,
            latest_version=latest,
            status=status,
            checked_at=checked_at,
            documentation_url=documentation_url,
            release_notes_url=release_notes_url,
            update_command_hint=hint,
            detail=detail,
        ))

    if cache != original_cache:
        _write_cache(cache_file, cache)
    return tuple(results)
