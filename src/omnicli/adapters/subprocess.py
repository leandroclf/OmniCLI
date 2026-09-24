from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
from contextlib import ExitStack

from omnicli.adapters.base import ProviderAdapter, ProviderResponse
from omnicli.exceptions import ProviderError
from omnicli.models import ProviderConfig


class SubprocessAdapter(ProviderAdapter):
    """Adapter for a local, non-interactive AI CLI."""

    def __init__(self, provider_name: str, config: ProviderConfig, isolated_cwd: bool = False) -> None:
        self.provider_name = provider_name
        self.config = config
        self.isolated_cwd = isolated_cwd

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
        if self.config.inherit_environment:
            environment = os.environ.copy()
        else:
            environment = {
                key: os.environ[key]
                for key in self.config.environment_allowlist
                if key in os.environ
            }
        environment.update(self.config.environment)
        return environment

    def _ensure_available(self) -> None:
        if not self.config.enabled:
            raise ProviderError(f"Provedor desabilitado: {self.provider_name}")
        if shutil.which(self.config.command, path=self._environment().get("PATH")) is None:
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

    def check_capabilities(self) -> str:
        """Check documented command markers using a safe help invocation.

        This never sends a prompt, starts a session, or requests model output.
        The markers are intentionally declared in configuration because each
        provider owns its own command vocabulary.
        """
        self._ensure_available()
        if not self.config.required_capabilities:
            return "não declarado"
        try:
            result = subprocess.run(
                [self.config.command, *self.config.capability_args],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                env=self._environment(),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ProviderError(f"Não foi possível consultar capacidades de {self.provider_name}: {exc}") from exc
        output = f"{result.stdout}\n{result.stderr}".casefold()
        missing = [marker for marker in self.config.required_capabilities if marker.casefold() not in output]
        if result.returncode != 0 or missing:
            missing_text = ", ".join(missing) if missing else "resposta de ajuda inválida"
            raise ProviderError(
                f"Contrato de capacidades incompatível para {self.provider_name}; ausente: {missing_text}"
            )
        return ", ".join(self.config.required_capabilities)

    def run(self, prompt: str, timeout_seconds: float) -> ProviderResponse:
        self._ensure_available()
        command, stdin = self.invocation(prompt)
        with ExitStack() as stack:
            working_dir = (
                stack.enter_context(tempfile.TemporaryDirectory(prefix="omnicli-provider-"))
                if self.isolated_cwd else None
            )
            stdout_file = stack.enter_context(tempfile.TemporaryFile(mode="w+b"))
            stderr_file = stack.enter_context(tempfile.TemporaryFile(mode="w+b"))
            try:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    env=self._environment(),
                    cwd=working_dir,
                    start_new_session=os.name == "posix",
                )
                try:
                    process.communicate(
                        input=stdin.encode("utf-8") if stdin is not None else None,
                        timeout=timeout_seconds,
                    )
                except subprocess.TimeoutExpired as exc:
                    self._terminate(process)
                    process.communicate()
                    raise ProviderError(
                        f"Timeout ao executar {self.provider_name} após {timeout_seconds:.0f}s"
                    ) from exc
            except OSError as exc:
                raise ProviderError(f"Falha ao iniciar {self.provider_name}: {exc}") from exc
            stdout_file.flush()
            stderr_file.flush()
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout_bytes = stdout_file.read(self.config.max_output_chars + 1)
            stderr_bytes = stderr_file.read(self.config.max_stderr_chars + 1)
            if len(stdout_bytes) > self.config.max_output_chars:
                raise ProviderError(
                    f"{self.provider_name} excedeu max_output_chars={self.config.max_output_chars}"
                )
            if len(stderr_bytes) > self.config.max_stderr_chars:
                raise ProviderError(
                    f"{self.provider_name} excedeu max_stderr_chars={self.config.max_stderr_chars}"
                )
            return ProviderResponse(
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
                exit_code=process.returncode or 0,
            )

    @staticmethod
    def _terminate(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None
