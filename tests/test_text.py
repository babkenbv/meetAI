from meetai.text import clean_transcript


def test_strips_leading_dash_and_trailing_ellipsis():
    assert clean_transcript("- Ի՞նչպես ես…") == "Ի՞նչպես ես"
    assert clean_transcript("- Բարև.") == "Բարև."
    assert clean_transcript("Լավ եմ...") == "Լավ եմ"


def test_keeps_armenian_punctuation_and_inner_words():
    assert clean_transcript("Լավը,- շնորհակալություն։") == "Լավը,- շնորհակալություն։"
    assert clean_transcript("Ինչպե՞ս ես") == "Ինչպե՞ս ես"


def test_collapses_spaces_and_handles_only_artifacts():
    assert clean_transcript("  a   b  ") == "a b"
    assert clean_transcript("- …") == ""
