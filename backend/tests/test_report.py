"""Citation integrity: a citation must only ever point at a source we actually retrieved."""

import pytest

from app.core.exceptions import ReportGenerationError
from app.services.extraction import RetrievedSource
from app.services.report import (
    build_reference_list,
    build_source_material,
    report_service,
    validate_citations,
)


def _source(n, url=None, content="body", snippet=None):
    return RetrievedSource(
        title=f"Source {n}",
        url=url or f"https://site{n}.com/page",
        domain=f"site{n}.com",
        source_type="Web article",
        snippet=f"snippet {n}" if snippet is None else snippet,
        content=content,
        retrieval_method="firecrawl" if content else "tavily_snippet",
        search_score=0.5,
    )


# ---------------------------------------------------------------- validate_citations


def test_citations_inside_range_are_kept():
    body = "Fact one [1]. Fact two [3]."
    assert validate_citations(body, 3) == body


def test_citation_past_the_end_is_removed():
    out = validate_citations("Real [1]. Invented [99].", 2)
    assert "[1]" in out
    assert "99" not in out


def test_zero_citation_is_removed():
    assert "0" not in validate_citations("Bad [0].", 3)


def test_all_citations_removed_when_no_sources():
    assert validate_citations("A [1] B [2].", 0) == "A  B ."


def test_surviving_citations_are_not_renumbered():
    """The bug this guards: compacting numbering re-points claims at the wrong page."""
    out = validate_citations("Claim about the seventh source [7].", 8)
    assert "[7]" in out
    assert "[1]" not in out


def test_gaps_in_numbering_survive_removals():
    out = validate_citations("A [1] B [2] C [4]", 4)
    assert "[1]" in out and "[2]" in out and "[4]" in out


def test_body_without_citations_is_untouched():
    body = "## Answer\nNo numbers here at all."
    assert validate_citations(body, 3) == body


def test_citations_within_sentences_and_lists():
    out = validate_citations("- point [1]\n- point [2] and [5]", 3)
    assert "[1]" in out and "[2]" in out
    assert "5]" not in out


# ---------------------------------------------------------------- reference list


def test_reference_list_is_built_from_stored_sources_only():
    sources = [_source(1), _source(2)]
    refs = build_reference_list(sources)
    assert "https://site1.com/page" in refs
    assert "https://site2.com/page" in refs
    assert refs.startswith("1. [Source 1]")


def test_reference_list_labels_snippet_only_sources():
    sources = [_source(1, content=""), _source(2, content="real")]
    refs = build_reference_list(sources)
    assert "search snippet only" in refs
    assert "full page" in refs


def test_reference_list_is_empty_for_no_sources():
    assert build_reference_list([]) == ""


# ---------------------------------------------------------------- source material


def test_source_material_is_numbered_and_labelled():
    material = build_source_material([_source(1), _source(2)])
    assert "[1]" in material and "[2]" in material
    assert "Full page text" in material
    assert "https://site1.com/page" in material


def test_source_material_skips_empty_sources():
    assert build_source_material([_source(1, content="", snippet="")]) == ""


def test_source_material_respects_total_budget():
    big = [_source(i, content="y" * 5000) for i in range(1, 9)]
    material = build_source_material(big)
    assert len(material) < 8 * 5000


# ---------------------------------------------------------------- report generation


class _FakeLLM:
    def __init__(self, body):
        self.body = body
        self.calls = []

    async def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=4096):
        self.calls.append((prompt, system_prompt))
        return self.body


async def test_report_appends_references_from_sources(monkeypatch):
    fake = _FakeLLM("## Answer\nGenerative AI raises privacy risks [1].")
    monkeypatch.setattr("app.services.report.llm_service", fake)

    result = await report_service.write_report(
        "What are the risks?", [_source(1), _source(2)]
    )
    assert "## References" in result.answer_markdown
    assert "https://site1.com/page" in result.answer_markdown
    assert "https://site2.com/page" in result.answer_markdown
    assert result.title == "What are the risks"


async def test_report_strips_fabricated_citations(monkeypatch):
    fake = _FakeLLM("Real claim [1]. Made-up source [42].")
    monkeypatch.setattr("app.services.report.llm_service", fake)

    result = await report_service.write_report("q?", [_source(1)])
    assert "[1]" in result.answer_markdown
    assert "[42]" not in result.answer_markdown


async def test_report_model_never_sees_a_reference_instruction(monkeypatch):
    """The model must not be asked to emit URLs or references; we build them."""
    fake = _FakeLLM("Answer [1].")
    monkeypatch.setattr("app.services.report.llm_service", fake)
    await report_service.write_report("q?", [_source(1)])
    _, system_prompt = fake.calls[0]
    assert "Never write URLs" in system_prompt


async def test_report_raises_without_sources():
    with pytest.raises(ReportGenerationError):
        await report_service.write_report("q?", [])


async def test_report_raises_on_empty_model_output(monkeypatch):
    monkeypatch.setattr("app.services.report.llm_service", _FakeLLM("   "))
    with pytest.raises(ReportGenerationError):
        await report_service.write_report("q?", [_source(1)])


async def test_report_wraps_llm_failure(monkeypatch):
    class _Boom:
        async def generate(self, *a, **kw):
            raise RuntimeError("groq down")

    monkeypatch.setattr("app.services.report.llm_service", _Boom())
    with pytest.raises(ReportGenerationError):
        await report_service.write_report("q?", [_source(1)])


def test_title_is_derived_from_the_question():
    from app.services.report import _derive_title

    assert _derive_title("What is AI?") == "What is AI"
    long = "word " * 60
    assert len(_derive_title(long)) <= 90
    assert _derive_title("  ") == "Research Report"

def test_fullwidth_citation_brackets_are_normalised():
    """openai/gpt-oss-120b writes 【3】; it must still become a real citation."""
    out = validate_citations("Fact one 【1】. Fact two 【3】.", 3)
    assert "[1]" in out and "[3]" in out
    assert "【" not in out


def test_fullwidth_citation_out_of_range_is_removed():
    out = validate_citations("Real 【1】. Invented 【77】.", 2)
    assert "[1]" in out
    assert "77" not in out


def test_mixed_bracket_styles_are_normalised_together():
    out = validate_citations("A [1] B 【2】 C ［3］", 3)
    assert "[1]" in out and "[2]" in out and "[3]" in out


def test_markdown_links_are_not_mangled_by_citation_normalising():
    body = "See [1](https://example.com/page) for details."
    assert validate_citations(body, 3) == body


def test_firecrawl_style_citation_markers_become_real_citations():
    """The model emits 【2†L1-L4】 on its own; it must resolve to source 2."""
    out = validate_citations("Risk A 【1†L1-L9】 and risk B 【3†L2-L4】.", 3)
    assert "[1]" in out and "[3]" in out
    assert "†" not in out


def test_firecrawl_style_marker_out_of_range_is_removed():
    out = validate_citations("Real 【1†L1-L4】. Invented 【42†L1-L9】.", 2)
    assert "[1]" in out
    assert "42" not in out and "†" not in out


def test_all_citation_forms_together():
    out = validate_citations("A [1] B 【2†Lx】 C 【3】 D [4]", 4)
    assert "[1]" in out and "[2]" in out and "[3]" in out and "[4]" in out

