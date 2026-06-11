"""
Tests for src/ingestion/sop_extractor.py

Key things to validate:
  - Does parse_sop_steps() correctly map a Layout AnalyzeResult to our schema?
  - Are page-furniture paragraphs (headers/footers/page numbers) skipped?
  - Does section tracking follow title/sectionHeading paragraphs?
  - Are wait/cure instructions classified as "duration" with correct seconds?
  - Are figures attached to steps on the same page?

Run smoke test against the real Prusa manual:
  python scripts/test_sop_pipeline.py --file tests/fixtures/prusa_mk3s_plus_assembly.pdf --pages 1-20

Owner: Person A (SOP pipeline)
"""
import pytest
from src.ingestion.sop_extractor import _classify_check, _document_name, parse_sop_steps


# ── Unit tests (no Azure required) ──────────────────────────────────────────

def test_parse_returns_required_top_level_keys(mock_layout_result, sample_run_id):
    """parse_sop_steps output must contain all top-level schema keys."""
    result = parse_sop_steps(mock_layout_result, sample_run_id, "https://example.com/sop.pdf?sas=secret")
    assert set(result.keys()) == {
        "run_id", "sop_document", "extracted_at", "total_steps", "steps"
    }
    assert result["run_id"] == sample_run_id
    assert result["sop_document"] == "sop.pdf"  # SAS query stripped


def test_parse_step_keys_and_sequence(mock_layout_result, sample_run_id):
    """Each step must contain all schema keys, with 1-based contiguous sequence."""
    result = parse_sop_steps(mock_layout_result, sample_run_id, "sop.pdf")
    assert result["total_steps"] == len(result["steps"]) == 3
    for i, step in enumerate(result["steps"]):
        assert set(step.keys()) == {
            "step_id", "sequence", "description", "check_type",
            "expected_duration_seconds", "section", "visual_references",
        }
        assert step["sequence"] == i + 1
        assert step["step_id"] == f"step-{str(i + 1).zfill(3)}"


def test_parse_skips_page_furniture_and_short_paragraphs(mock_layout_result, sample_run_id):
    """Headers, footers, page numbers, and short part labels must not become steps."""
    result = parse_sop_steps(mock_layout_result, sample_run_id, "sop.pdf")
    descriptions = [s["description"] for s in result["steps"]]
    assert "Prusa Research" not in descriptions          # pageHeader
    assert "Page 12" not in descriptions                 # pageNumber
    assert "3x M3x10 screw" not in descriptions          # below _MIN_STEP_CHARS


def test_parse_tracks_sections(mock_layout_result, sample_run_id):
    """Steps must carry the most recent sectionHeading; headings are not steps."""
    result = parse_sop_steps(mock_layout_result, sample_run_id, "sop.pdf")
    sections = [s["section"] for s in result["steps"]]
    assert sections == ["2.1 Y-Axis Assembly", "2.1 Y-Axis Assembly", "2.2 Y-Axis Belt"]
    descriptions = [s["description"] for s in result["steps"]]
    assert "2.1 Y-Axis Assembly" not in descriptions


def test_parse_duration_step(mock_layout_result, sample_run_id):
    """A cure/wait instruction with a time quantity becomes a duration check."""
    result = parse_sop_steps(mock_layout_result, sample_run_id, "sop.pdf")
    duration_steps = [s for s in result["steps"] if s["check_type"] == "duration"]
    assert len(duration_steps) == 1
    assert duration_steps[0]["expected_duration_seconds"] == 30
    presence_steps = [s for s in result["steps"] if s["check_type"] == "presence"]
    assert all(s["expected_duration_seconds"] is None for s in presence_steps)


def test_parse_attaches_same_page_figures(mock_layout_result, sample_run_id):
    """Steps reference figures detected on the same page."""
    result = parse_sop_steps(mock_layout_result, sample_run_id, "sop.pdf")
    assert result["steps"][0]["visual_references"] == ["figure-1.1", "figure-1.2"]
    assert result["steps"][2]["visual_references"] == []  # page 2 has no figures


def test_parse_skips_table_of_contents_body(sample_run_id):
    """TOC entries are step titles, not instructions — they must not become steps."""
    paragraphs = [
        _MockParagraph("Table of Contents", role="sectionHeading", page=2),
        _MockParagraph("Step 1 - All the required tools are included", page=2),
        _MockParagraph("Step 2 - Important: Electronics protection notes", page=2),
        _MockParagraph("2.1 Y-Axis Assembly", role="sectionHeading", page=20),
        _MockParagraph("Attach the Y-axis motor to the frame using M3x10 screws.", page=20),
    ]
    result = parse_sop_steps(_MockResult(paragraphs, []), sample_run_id, "sop.pdf")
    assert result["total_steps"] == 1
    assert result["steps"][0]["section"] == "2.1 Y-Axis Assembly"


def test_parse_section_granularity_merges_paragraphs(mock_layout_result, sample_run_id):
    """In section mode, consecutive paragraphs under one heading merge into one step."""
    result = parse_sop_steps(mock_layout_result, sample_run_id, "sop.pdf", granularity="section")
    assert result["total_steps"] == 2
    first, second = result["steps"]
    assert first["section"] == "2.1 Y-Axis Assembly"
    assert "Attach the Y-axis motor" in first["description"]
    assert "Allow adhesive to cure" in first["description"]
    # Merged step inherits duration from any constituent paragraph
    assert first["check_type"] == "duration"
    assert first["expected_duration_seconds"] == 30
    # Figure refs are deduplicated across merged paragraphs
    assert first["visual_references"] == ["figure-1.1", "figure-1.2"]
    assert second["section"] == "2.2 Y-Axis Belt"
    assert second["sequence"] == 2


def test_parse_rejects_unknown_granularity(mock_layout_result, sample_run_id):
    with pytest.raises(ValueError, match="granularity"):
        parse_sop_steps(mock_layout_result, sample_run_id, "sop.pdf", granularity="page")


def test_parse_empty_result(sample_run_id):
    """An empty AnalyzeResult yields zero steps, not an exception."""
    result = parse_sop_steps(_MockResult([], []), sample_run_id, "sop.pdf")
    assert result["total_steps"] == 0
    assert result["steps"] == []


@pytest.mark.parametrize(
    "text,expected_type,expected_seconds",
    [
        ("Allow adhesive to cure for minimum 30 seconds before proceeding.", "duration", 30),
        ("Let it rest for 5 minutes before the next step.", "duration", 300),
        ("Leave the bed to cool for 1 hour.", "duration", 3600),
        ("Attach the Y-axis motor using M3x10 screws. Torque to 0.4 Nm.", "presence", None),
        # Time quantity without a wait cue stays presence — timing is incidental
        ("Tighten each screw for 2 seconds at the end of the pass.", "presence", None),
    ],
)
def test_classify_check(text, expected_type, expected_seconds):
    assert _classify_check(text) == (expected_type, expected_seconds)


def test_document_name():
    assert _document_name("https://acct.blob.core.windows.net/sop/manual.pdf?sv=abc") == "manual.pdf"
    assert _document_name(r"tests\fixtures\prusa_mk3s_plus_assembly.pdf") == "prusa_mk3s_plus_assembly.pdf"


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_run_id():
    return "run-test-00000001"


class _MockRegion:
    def __init__(self, page_number):
        self.page_number = page_number


class _MockParagraph:
    """Minimal stand-in for DocumentParagraph returned by the SDK."""
    def __init__(self, content, role=None, page=1):
        self.content = content
        self.role = role
        self.bounding_regions = [_MockRegion(page)]


class _MockFigure:
    """Minimal stand-in for DocumentFigure."""
    def __init__(self, figure_id, page):
        self.id = figure_id
        self.bounding_regions = [_MockRegion(page)]


class _MockResult:
    def __init__(self, paragraphs, figures):
        self.paragraphs = paragraphs
        self.figures = figures
        self.pages = []


@pytest.fixture
def mock_layout_result():
    paragraphs = [
        _MockParagraph("Prusa Research", role="pageHeader", page=1),
        _MockParagraph("Original Prusa i3 MK3S+ Assembly Manual", role="title", page=1),
        _MockParagraph("2.1 Y-Axis Assembly", role="sectionHeading", page=1),
        _MockParagraph("3x M3x10 screw", page=1),  # part label — too short
        _MockParagraph(
            "Attach the Y-axis motor to the frame using M3x10 screws. Torque to 0.4 Nm.",
            page=1,
        ),
        _MockParagraph(
            "Allow adhesive to cure for minimum 30 seconds before proceeding.",
            page=1,
        ),
        _MockParagraph("Page 12", role="pageNumber", page=1),
        _MockParagraph("2.2 Y-Axis Belt", role="sectionHeading", page=2),
        _MockParagraph(
            "Thread the Y-axis belt through the motor pulley. Belt must be taut with no slack.",
            page=2,
        ),
    ]
    figures = [
        _MockFigure("1.1", page=1),
        _MockFigure("1.2", page=1),
    ]
    return _MockResult(paragraphs, figures)
