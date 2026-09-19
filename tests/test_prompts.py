from omnicli.models import StageConfig
from omnicli.prompts import build_stage_prompt


def test_prompt_preserves_idea_and_previous_output() -> None:
    stage = StageConfig(name="review", provider="test", role="Reviewer", instruction="Review")
    prompt = build_stage_prompt(stage, "Minha ideia", "Saída anterior", 1, 2)
    assert "Minha ideia" in prompt
    assert "Saída anterior" in prompt
    assert "não concorde automaticamente" in prompt
    assert "ciclo 1 de 2" in prompt
