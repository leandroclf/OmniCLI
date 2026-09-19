from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderResponse:
    stdout: str
    stderr: str
    exit_code: int
    version: str | None = None


class ProviderAdapter(ABC):
    provider_name: str

    @abstractmethod
    def check(self) -> str:
        """Return the provider version or raise a provider error."""

    def check_capabilities(self) -> str:
        """Return a non-interactive capability check or raise a provider error.

        Adapters that do not expose a help-surface contract can keep the default
        implementation. This keeps provider capability checks additive for
        custom adapters.
        """
        return "não declarado"

    @abstractmethod
    def run(self, prompt: str, timeout_seconds: float) -> ProviderResponse:
        """Run a prompt through the provider."""
