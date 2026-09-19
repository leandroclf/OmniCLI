import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "bootstrap.sh"


def test_bootstrap_script_has_valid_shell_syntax() -> None:
    result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_bootstrap_defaults_to_safe_plan_mode() -> None:
    result = subprocess.run(["bash", str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "modo plan" in result.stdout
    assert "nenhuma alteração será feita" in result.stdout


def test_bootstrap_help_mentions_safe_provider_checks() -> None:
    result = subprocess.run(["bash", str(SCRIPT), "--help"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
    assert "--providers" in result.stdout
    assert "--official-docs" in result.stdout
    assert "--refine" in result.stdout
