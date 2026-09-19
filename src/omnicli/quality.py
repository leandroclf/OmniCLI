from __future__ import annotations

from dataclasses import dataclass

REQUIRED_SECTIONS = ("escopo", "risco", "critério", "decis")


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
    found = sum(1 for section in REQUIRED_SECTIONS if section in normalized)
    score = min(100, found * 20 + (20 if len(document.strip()) >= 1000 else 0))
    if len(document.strip()) < 300:
        warnings.append("A saída final é muito curta para uma proposta arquitetural.")
    if "decis" not in normalized:
        warnings.append("Não foi encontrada uma seção de decisões pendentes.")
    if "risco" not in normalized:
        warnings.append("Não foi encontrada uma seção de riscos.")
    return QualityReport(score=score, warnings=tuple(warnings))
