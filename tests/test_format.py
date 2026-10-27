from meetai.format import format_line
from meetai.types import Line, Source


def line(confident):
    return Line(1.0, 2.0, Source.MIC, "Me", "hy", "Հանը", "en", "What is the meaning of life?", 1.0, confident)


def test_confident_line_has_no_marker():
    assert "[unsure]" not in format_line(line(True))
    assert "EN: What is the meaning of life?" in format_line(line(True))


def test_unsure_line_is_marked():
    assert "EN: [unsure] What is the meaning of life?" in format_line(line(False))
