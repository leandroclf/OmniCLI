from omnicli.quality import assess_document


def test_quality_accepts_english_section_names() -> None:
    document = "# Scope\n# Risks\n# Acceptance criteria\n# Pending decisions\n" + ("detail " * 160)
    report = assess_document(document)
    assert report.score == 100
    assert report.passed
