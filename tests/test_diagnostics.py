import sys

from omnicli.diagnostics import diagnose
from omnicli.models import OmniConfig, PipelineConfig, ProviderConfig, StageConfig


def _config(provider: ProviderConfig) -> OmniConfig:
    return OmniConfig(
        pipeline=PipelineConfig(
            stages=[StageConfig(name="review", provider="python", role="Reviewer", instruction="Review")]
        ),
        providers={"python": provider},
    )


def test_doctor_reports_ready_provider() -> None:
    report = diagnose(
        _config(ProviderConfig(command=sys.executable, args=["-c", "print('ok')", "{prompt}"])),
    )
    assert report.ready
    assert report.providers[0].transport == "argv"
    assert report.providers[0].status == "ready"


def test_doctor_fails_when_required_provider_is_disabled() -> None:
    report = diagnose(_config(ProviderConfig(command=sys.executable, enabled=False)))
    assert not report.ready
    assert report.providers[0].status == "disabled"
