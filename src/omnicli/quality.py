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

    @property
    def passed(self) -> bool:
        return self.score >= 50


def assess_document(document: str) -> QualityReport:
    normalized = document.casefold()
    warnings: list[str] = []
    found = sum(1 for variants in REQUIRED_CONCEPTS if any(variant in normalized for variant in variants))
    score = min(100, found * 20 + (20 if len(document.strip()) >= 1000 else 0))
    if len(document.strip()) < 300:
        warnings.append("A saída final é muito curta para uma proposta arquitetural.")
    if not any(value in normalized for value in ("decis", "decision")):
        warnings.append("Não foi encontrada uma seção de decisões pendentes.")
    if not any(value in normalized for value in ("risco", "risk")):
        warnings.append("Não foi encontrada uma seção de riscos.")
    return QualityReport(score=score, warnings=tuple(warnings))
