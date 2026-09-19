class OmniCLIError(Exception):
    """Base exception for expected OmniCLI failures."""


class ConfigurationError(OmniCLIError):
    """Raised when the pipeline configuration is invalid."""


class ProviderError(OmniCLIError):
    """Raised when a provider cannot be executed or understood."""


class PipelineError(OmniCLIError):
    """Raised when a pipeline stage fails."""
