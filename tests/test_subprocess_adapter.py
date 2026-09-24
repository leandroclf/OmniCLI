import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from omnicli.adapters.subprocess import SubprocessAdapter
from omnicli.exceptions import ProviderError
from omnicli.models import ProviderConfig


def test_argument_transport_preserves_prompt_as_one_argument() -> None:
    config = ProviderConfig(
        command=sys.executable,
        args=["-c", "import sys; print(sys.argv[1])", "{prompt}"],
    )
    adapter = SubprocessAdapter("python", config)
    prompt = "texto com espaços; $(não executar)"
    response = adapter.run(prompt, timeout_seconds=5)
    assert response.exit_code == 0
    assert response.stdout.strip() == prompt


def test_stdin_transport_remains_available_for_custom_clis() -> None:
    config = ProviderConfig(
        command=sys.executable,
        args=["-c", "import sys; print(sys.stdin.read())"],
    )
    response = SubprocessAdapter("python", config).run("via stdin", timeout_seconds=5)
    assert response.stdout.strip() == "via stdin"


def test_codebase_mode_runs_provider_in_temporary_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "private.py").write_text("local only", encoding="utf-8")
    config = ProviderConfig(
        command=sys.executable,
        args=["-c", "import os; print(os.path.exists('private.py')); print(os.getcwd())", "{prompt}"],
    )
    response = SubprocessAdapter("python", config, isolated_cwd=True).run("context", timeout_seconds=5)
    visible, working_dir = response.stdout.strip().splitlines()
    assert visible == "False"
    assert Path(working_dir) != tmp_path
    assert not Path(working_dir).exists()


def test_prompt_size_limit_is_enforced() -> None:
    config = ProviderConfig(command=sys.executable, max_prompt_chars=1_000)
    with pytest.raises(ProviderError, match="max_prompt_chars"):
        SubprocessAdapter("python", config).invocation("x" * 1_001)


def test_embedded_prompt_placeholder_is_rejected() -> None:
    with pytest.raises(ValidationError, match="isolated argument"):
        ProviderConfig(command="tool", args=["--prompt={prompt}"])


def test_capability_probe_uses_help_arguments_without_prompt() -> None:
    config = ProviderConfig(
        command=sys.executable,
        capability_args=["-c", "print('-p --output-format')"],
        required_capabilities=["-p", "--output-format"],
    )
    result = SubprocessAdapter("python", config).check_capabilities()
    assert result == "-p, --output-format"


def test_capability_probe_reports_missing_marker() -> None:
    config = ProviderConfig(
        command=sys.executable,
        capability_args=["-c", "print('-p')"],
        required_capabilities=["-p", "--output-format"],
    )
    with pytest.raises(ProviderError, match="--output-format"):
        SubprocessAdapter("python", config).check_capabilities()


def test_output_limit_is_enforced_without_shell_execution() -> None:
    config = ProviderConfig(
        command=sys.executable,
        args=["-c", "print('x' * 2000)", "{prompt}"],
        max_output_chars=1_000,
    )

    with pytest.raises(ProviderError, match="max_output_chars"):
        SubprocessAdapter("python", config).run("prompt", timeout_seconds=5)


def test_provider_environment_is_minimal_by_default() -> None:
    config = ProviderConfig(
        command=sys.executable,
        inherit_environment=False,
        environment_allowlist=[],
        environment={"PROVIDER_TOKEN": "configured"},
    )

    environment = SubprocessAdapter("python", config)._environment()

    assert environment == {"PROVIDER_TOKEN": "configured"}
