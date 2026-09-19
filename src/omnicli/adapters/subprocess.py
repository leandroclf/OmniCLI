from __future__ import annotations

import os
import shutil
import subprocess

from omnicli.adapters.base import ProviderAdapter, ProviderResponse
from omnicli.exceptions import ProviderError
from omnicli.models import ProviderConfig


class SubprocessAdapter(ProviderAdapter):
    """Adapter for a local, non-interactive AI CLI."""

    def __init__(self, provider_name: str, config: ProviderConfig) -> None:
        self.provider_name = provider_name
        self.config = config

    @property
    def command(self) -> list[str]:
        return [self.config.command, *self.config.args]

    def _environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(self.config.environment)
        return environment

    def _ensure_available(self) -> None:
        if not self.config.enabled:
            raise ProviderError(f"Provedor desabilitado: {self.provider_name}")
        if shutil.which(self.config.command) is None:
            raise ProviderError(
                f"CLI não encontrada para {self.provider_name}: {self.config.command}. "
                "Instale-a e autentique-a antes de executar o pipeline."
            )

    def check(self) -> str:
        self._ensure_available()
        try:
            result = subprocess.run(
                [self.config.command, *self.config.version_args],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                env=self._environment(),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ProviderError(f"Não foi possível consultar {self.provider_name}: {exc}") from exc
        version = (result.stdout or result.stderr).strip().splitlines()
        if result.returncode != 0 or not version:
            raise ProviderError(f"A CLI {self.provider_name} não respondeu corretamente à verificação de versão")
        return version[0][:300]

    def run(self, prompt: str, timeout_seconds: float) -> ProviderResponse:
        self._ensure_available()
        try:
            process = subprocess.run(
                self.command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                env=self._environment(),
            )
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(f"Timeout ao executar {self.provider_name} após {timeout_seconds:.0f}s") from exc
        except OSError as exc:
            raise ProviderError(f"Falha ao iniciar {self.provider_name}: {exc}") from exc
        return ProviderResponse(
            stdout=process.stdout or "",
            stderr=process.stderr or "",
            exit_code=process.returncode,
        )


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None
