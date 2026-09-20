import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
VALIDATOR = ROOT / "scripts/validate-benchmark-result.py"
EXAMPLE = ROOT / "docs/benchmarks/human-quality-v1-result.example.yaml"


def test_benchmark_result_example_is_valid() -> None:
    result = subprocess.run([sys.executable, str(VALIDATOR), str(EXAMPLE)], capture_output=True, text=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert '"valid": true' in result.stdout


def test_benchmark_validator_rejects_provider_identity(tmp_path: Path) -> None:
    content = EXAMPLE.read_text(encoding="utf-8") + "\nprovider: codex\n"
    result_file = tmp_path / "result.yaml"
    result_file.write_text(content, encoding="utf-8")

    result = subprocess.run([sys.executable, str(VALIDATOR), str(result_file)], capture_output=True, text=True)

    assert result.returncode == 1
    assert "identificador proibido" in result.stdout
