from __future__ import annotations

from omnicli.models import StageConfig


def build_stage_prompt(
    stage: StageConfig,
    idea: str,
    previous_output: str,
    loop: int,
    total_loops: int,
) -> str:
    previous = previous_output.strip() or "Ainda não existe uma saída anterior."
    return f"""Você participa do pipeline OmniCLI como: {stage.role}.

Objetivo desta etapa: {stage.instruction}

Regras:
- Seja construtivo, mas não concorde automaticamente com premissas frágeis.
- Separe fatos fornecidos, hipóteses e recomendações.
- Não invente integrações, custos, leis ou capacidades de ferramentas sem sinalizar a incerteza.
- Preserve decisões válidas do contexto, mas corrija inconsistências explicitamente.
- Responda em Markdown, com títulos claros e conteúdo acionável.
- Este é o ciclo {loop} de {total_loops}.

IDEIA ORIGINAL:
{idea}

SAÍDA DA ETAPA ANTERIOR:
{previous}

Produza somente o resultado desta etapa, sem comentar o funcionamento interno do OmniCLI.
"""
