from __future__ import annotations

from dataclasses import asdict, dataclass

from omnicli.adapters.subprocess import SubprocessAdapter, command_exists
from omnicli.exceptions import OmniCLIError
from omnicli.models import OmniConfig


@dataclass(frozen=True)
class ProviderDiagnostic:
    name: str
    command: str
    required: bool
    enabled: bool
    transport: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str | bool]:
        return asdict(self)


@dataclass(frozen=True)
class DoctorReport:
    ready: bool
    providers: tuple[ProviderDiagnostic, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "providers": [provider.as_dict() for provider in self.providers],
        }


def diagnose(config: OmniConfig, check_versions: bool = True) -> DoctorReport:
    required = {stage.provider for stage in config.pipeline.stages}
    diagnostics: list[ProviderDiagnostic] = []
    ready = True

    for name, provider in config.providers.items():
        is_required = name in required
        transport = "argv" if "{prompt}" in provider.args else "stdin"
        status = "ready"
        detail = "configuração válida"

        if not provider.enabled:
            status = "disabled"
            detail = "provedor desabilitado"
        elif not command_exists(provider.command):
            status = "missing"
            detail = "comando não encontrado no PATH"
        elif check_versions:
            try:
                detail = SubprocessAdapter(name, provider).check()
            except OmniCLIError as exc:
                status = "error"
                detail = str(exc)

        if is_required and status != "ready":
            ready = False
        diagnostics.append(
            ProviderDiagnostic(
                name=name,
                command=provider.command,
                required=is_required,
                enabled=provider.enabled,
                transport=transport,
                status=status,
                detail=detail,
            )
        )

    return DoctorReport(ready=ready, providers=tuple(diagnostics))
