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

    @abstractmethod
    def run(self, prompt: str, timeout_seconds: float) -> ProviderResponse:
        """Run a prompt through the provider."""
