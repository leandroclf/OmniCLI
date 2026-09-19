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

    def invocation(self, prompt: str) -> tuple[list[str], str | None]:
        """Build a shell-free invocation and select argv or stdin transport."""
        if "\x00" in prompt:
            raise ProviderError(f"O prompt de {self.provider_name} contém um caractere NUL inválido")
        if len(prompt) > self.config.max_prompt_chars:
            raise ProviderError(
                f"O prompt de {self.provider_name} excede max_prompt_chars="
                f"{self.config.max_prompt_chars} ({len(prompt)} caracteres)"
            )
        if any("{prompt}" in argument and argument != "{prompt}" for argument in self.config.args):
            raise ProviderError("Use {prompt} como argumento isolado; placeholders embutidos não são permitidos")
        has_placeholder = "{prompt}" in self.config.args
        args = [prompt if argument == "{prompt}" else argument for argument in self.config.args]
        return [self.config.command, *args], None if has_placeholder else prompt

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
        command, stdin = self.invocation(prompt)
        try:
            process = subprocess.run(
                command,
                input=stdin,
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
