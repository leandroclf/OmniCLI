from __future__ import annotations

import re
from dataclasses import dataclass

QUALITY_EVALUATION_VERSION = "quality-v1"

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
    evidence: tuple[str, ...] = ()
    evaluation_version: str = QUALITY_EVALUATION_VERSION

    @property
    def passed(self) -> bool:
        return self.score >= 50

    @property
    def hard_gates_passed(self) -> bool:
        return not self.security_violations and not self.critical_contradictions

    def gate_passed(self, minimum_score: int) -> bool:
        return self.hard_gates_passed and self.score >= minimum_score and not self.missing_concepts

    def as_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "passed": self.passed,
            "hard_gates_passed": self.hard_gates_passed,
            "warnings": list(self.warnings),
            "missing_concepts": list(self.missing_concepts),
            "security_violations": list(self.security_violations),
            "critical_contradictions": list(self.critical_contradictions),
            "recommended_stage": self.recommended_stage,
            "evidence": list(self.evidence),
            "evaluation_version": self.evaluation_version,
        }


def assess_document(document: str) -> QualityReport:
    normalized = document.casefold()
    warnings: list[str] = []
    evidence: list[str] = []
    headings = tuple(
        heading.casefold()
        for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", document)
    )
    missing = tuple(
        variants[0]
        for variants in REQUIRED_CONCEPTS
        if not any(variant in normalized for variant in variants)
    )
    found = len(REQUIRED_CONCEPTS) - len(missing)
    for label, variants in REQUIRED_CONCEPTS:
        if any(variant in normalized for variant in variants):
            evidence.append(label)
    if headings:
        evidence.append(f"headings:{len(headings)}")
    else:
        warnings.append("A proposta não contém títulos Markdown identificáveis.")
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
        evidence=tuple(evidence),
    )
