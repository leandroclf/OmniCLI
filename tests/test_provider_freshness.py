from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from omnicli.cli import _provider_preflight, app
from omnicli.diagnostics import DoctorReport
from omnicli.exceptions import OmniCLIError
from omnicli.models import OmniConfig, PipelineConfig, ProviderConfig, StageConfig
from omnicli.provider_freshness import CACHE_TTL, ProviderFreshness, check_provider_freshness


def _config(installed_version: str = "1.2.0") -> OmniConfig:
    return OmniConfig(
        pipeline=PipelineConfig(stages=[StageConfig(
            name="test", provider="sample", role="test", instruction="test",
        )]),
        providers={"sample": ProviderConfig(
            command=sys.executable,
            version_args=["-c", f"print('sample {installed_version}')"],
            latest_version_url="https://official.example/latest",
            documentation_url="https://official.example/docs",
            release_notes_url="https://official.example/releases",
            update_command_hint="sample upgrade",
        )},
    )


def test_detects_official_update_and_caches_only_public_version_metadata(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    now = datetime(2026, 9, 24, tzinfo=timezone.utc)
    calls: list[str] = []

    def fetch(url: str) -> tuple[str, str]:
        calls.append(url)
        return "1.3.0", now.isoformat()

    result = check_provider_freshness(_config(), cache_path=cache_path, now=now, fetch=fetch)
    assert result[0].status == "update_available"
    assert result[0].installed_version == "1.2.0"
    assert result[0].latest_version == "1.3.0"
    assert result[0].documentation_url == "https://official.example/docs"
    assert result[0].update_command_hint == "sample upgrade"
    assert calls == ["https://official.example/latest"]
    assert json.loads(cache_path.read_text()) == {
        "https://official.example/latest": {"version": "1.3.0", "checked_at": now.isoformat()}
    }


def test_uses_fresh_cache_without_network(tmp_path: Path) -> None:
    now = datetime(2026, 9, 24, tzinfo=timezone.utc)
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"https://official.example/latest": {
        "version": "1.2.0", "checked_at": (now - CACHE_TTL + timedelta(minutes=1)).isoformat(),
    }}))

    def fail_fetch(_url: str) -> tuple[str, str]:
        raise AssertionError("fresh metadata cache must avoid network")

    result = check_provider_freshness(_config(), cache_path=cache_path, now=now, fetch=fail_fetch)
    assert result[0].status == "current"


def test_network_failure_uses_old_cache_and_reports_uncertainty(tmp_path: Path) -> None:
    now = datetime(2026, 9, 24, tzinfo=timezone.utc)
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"https://official.example/latest": {
        "version": "1.3.0", "checked_at": (now - CACHE_TTL - timedelta(hours=2)).isoformat(),
    }}))

    def fail_fetch(_url: str) -> tuple[str, str]:
        raise OSError("offline")

    result = check_provider_freshness(_config(), cache_path=cache_path, now=now, fetch=fail_fetch)
    assert result[0].status == "update_available"
    assert "usando cache anterior" in result[0].detail


def test_strict_comparison_does_not_trust_expired_cache_as_current(tmp_path: Path) -> None:
    now = datetime(2026, 9, 24, tzinfo=timezone.utc)
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(json.dumps({"https://official.example/latest": {
        "version": "1.2.0", "checked_at": (now - CACHE_TTL - timedelta(hours=1)).isoformat(),
    }}))

    def fail_fetch(_url: str) -> tuple[str, str]:
        raise OSError("offline")

    result = check_provider_freshness(_config(), cache_path=cache_path, now=now, fetch=fail_fetch)
    assert result[0].status == "unknown"
    assert "usando cache anterior" in result[0].detail


def test_unknown_provider_source_is_reported_without_external_call(tmp_path: Path) -> None:
    config = _config()
    config.providers["sample"].latest_version_url = None
    result = check_provider_freshness(config, cache_path=tmp_path / "cache.json")
    assert result[0].status == "unknown"
    assert "não declarada" in result[0].detail


def test_strict_startup_preflight_blocks_when_an_update_is_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("omnicli.cli.diagnose", lambda *_args, **_kwargs: DoctorReport(ready=True, providers=()))
    monkeypatch.setattr("omnicli.cli.check_provider_freshness", lambda _config: (
        ProviderFreshness("claude", "1.0.0", "1.1.0", "update_available", None,
                          "https://official.example/docs", "https://official.example/releases",
                          "official updater", "update exists"),
    ))
    with pytest.raises(OmniCLIError, match="--require-latest"):
        _provider_preflight(None, require_latest=True, skip_latest_check=False)


def test_default_startup_preflight_warns_and_keeps_available_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("omnicli.cli.diagnose", lambda *_args, **_kwargs: DoctorReport(ready=True, providers=()))
    monkeypatch.setattr("omnicli.cli.check_provider_freshness", lambda _config: (
        ProviderFreshness("claude", "1.0.0", "1.1.0", "update_available", None,
                          "https://official.example/docs", "https://official.example/releases",
                          "official updater", "update exists"),
    ))
    _provider_preflight(None, require_latest=False, skip_latest_check=False)


def test_providers_check_latest_json_includes_official_links(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("omnicli.cli.check_provider_freshness", lambda _config: (
        ProviderFreshness("claude", "1.1.0", "1.1.0", "current", "2026-09-24T00:00:00+00:00",
                          "https://official.example/docs", "https://official.example/releases",
                          "official updater", "current"),
    ))
    response = CliRunner().invoke(app, ["providers", "check", "--latest", "--json"])
    assert response.exit_code == 0
    assert "https://official.example/docs" in response.output
    assert "https://official.example/releases" in response.output
