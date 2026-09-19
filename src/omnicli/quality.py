from __future__ import annotations

from dataclasses import dataclass

REQUIRED_CONCEPTS = (
    ("escopo", "scope"),
    ("risco", "risk"),
    ("critério", "criter"),
    ("decis", "decision"),
)


@dataclass(frozen=True)
class QualityReport:
    score: int
    warnings: tuple[str, ...]
    missing_concepts: tuple[str, ...] = ()
    security_violations: tuple[str, ...] = ()
    critical_contradictions: tuple[str, ...] = ()
    recommended_stage: str | None = None

    @property
    def passed(self) -> bool:
        return self.score >= 50

    @property
    def hard_gates_passed(self) -> bool:
        return not self.security_violations and not self.critical_contradictions

    def gate_passed(self, minimum_score: int) -> bool:
        return self.hard_gates_passed and self.score >= minimum_score and not self.missing_concepts


def assess_document(document: str) -> QualityReport:
    normalized = document.casefold()
    warnings: list[str] = []
    missing = tuple(
        variants[0]
        for variants in REQUIRED_CONCEPTS
        if not any(variant in normalized for variant in variants)
    )
    found = len(REQUIRED_CONCEPTS) - len(missing)
    score = min(100, found * 20 + (20 if len(document.strip()) >= 1000 else 0))
    if len(document.strip()) < 300:
        warnings.append("A saída final é muito curta para uma proposta arquitetural.")
    if not any(value in normalized for value in ("decis", "decision")):
        warnings.append("Não foi encontrada uma seção de decisões pendentes.")
    if not any(value in normalized for value in ("risco", "risk")):
        warnings.append("Não foi encontrada uma seção de riscos.")

    security_violations = tuple(
        marker
        for marker in (
            "ignore previous instructions",
            "ignore all previous instructions",
            "reveal the system prompt",
            "reveal system prompt",
            "exfiltrate secrets",
            "execute arbitrary commands without approval",
            "ignore instruções anteriores",
            "ignore todas as instruções anteriores",
            "revele o prompt do sistema",
            "exfiltre segredos",
            "execute comandos arbitrários sem aprovação",
        )
        if marker in normalized
    )
    critical_contradictions = tuple(
        marker
        for marker in (
            "contradição crítica não resolvida",
            "critical contradiction unresolved",
            "unresolved critical contradiction",
        )
        if marker in normalized
    )
    if security_violations:
        warnings.append("Foram encontrados marcadores de instrução potencialmente insegura.")
    if critical_contradictions:
        warnings.append("A proposta declara contradições críticas não resolvidas.")

    if any(value in missing for value in ("escopo",)):
        recommended_stage = "discovery"
    elif missing:
        recommended_stage = "critical-review"
    else:
        recommended_stage = None

    return QualityReport(
        score=score,
        warnings=tuple(warnings),
        missing_concepts=missing,
        security_violations=security_violations,
        critical_contradictions=critical_contradictions,
        recommended_stage=recommended_stage,
    )
