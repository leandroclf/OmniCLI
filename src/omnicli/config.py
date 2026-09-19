from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import ValidationError

from omnicli.exceptions import ConfigurationError
from omnicli.models import OmniConfig, PipelineConfig, ProviderConfig, StageConfig

DEFAULT_CONFIG = OmniConfig(
    pipeline=PipelineConfig(
        stages=[
            StageConfig(
                name="discovery",
                provider="gemini",
                role="Explorador de produto",
                instruction=(
                    "Expanda a ideia inicial. Identifique problema, público-alvo, objetivos, "
                    "funcionalidades e perguntas ainda não respondidas. Não trate hipóteses como fatos."
                ),
            ),
            StageConfig(
                name="critical-review",
                provider="claude",
                role="Revisor crítico",
                instruction=(
                    "Questione as premissas da proposta, procure contradições, riscos, excesso de escopo, "
                    "dependências e decisões que precisam de validação humana. Sugira correções objetivas."
                ),
            ),
            StageConfig(
                name="architecture",
                provider="codex",
                role="Arquiteto de soluções",
                instruction=(
                    "Estruture uma arquitetura tecnicamente viável. Descreva componentes, fluxos, dados, "
                    "integrações, requisitos não funcionais, segurança, observabilidade e plano de implementação."
                ),
            ),
            StageConfig(
                name="feasibility",
                provider="gemini",
                role="Revisor de viabilidade",
                instruction=(
                    "Avalie a proposta arquitetural. Aponte custos, complexidade, riscos operacionais, "
                    "limitações das ferramentas e alternativas mais simples quando forem adequadas."
                ),
            ),
            StageConfig(
                name="master-proposal",
                provider="claude",
                role="Editor técnico",
                instruction=(
                    "Consolide uma Proposta Mestra de Arquitetura. Inclua escopo, premissas, decisões, "
                    "requisitos, arquitetura, riscos, critérios de aceite e uma seção de decisões pendentes."
                ),
            ),
        ]
    ),
    providers={
        "gemini": ProviderConfig(command="gemini"),
        "claude": ProviderConfig(command="claude"),
        "codex": ProviderConfig(command="codex"),
        "copilot": ProviderConfig(command="gh", args=["copilot"]),
    },
)


def _dump_model(model: Any) -> dict[str, Any]:
    return cast(dict[str, Any], model.model_dump(mode="json"))


def load_config(path: Path | None) -> OmniConfig:
    if path is None:
        return DEFAULT_CONFIG.model_copy(deep=True)
    if not path.exists():
        raise ConfigurationError(f"Arquivo de configuração não encontrado: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return OmniConfig.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ConfigurationError(f"Configuração inválida em {path}: {exc}") from exc


def write_example_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(_dump_model(DEFAULT_CONFIG), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
