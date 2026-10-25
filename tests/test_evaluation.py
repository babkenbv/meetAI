import numpy as np
import pytest

from meetai.evaluation import Sample, cer, edit_distance, evaluate_asr, normalize, wer


def test_normalize_strips_armenian_and_latin_punctuation():
    assert normalize("Բարև, ինչպե՞ս ես։") == "բարև ինչպես ես"
    assert normalize("  Hello,   WORLD! ") == "hello world"


def test_edit_distance():
    assert edit_distance(list("kitten"), list("sitting")) == 3
    assert edit_distance([], list("ab")) == 2


def test_wer_and_cer():
    assert wer("a b c d", "a b c d") == 0.0
    assert wer("a b c d", "a x c") == pytest.approx(0.5)
    assert cer("abcd", "abxd") == pytest.approx(0.25)


def test_empty_reference_fails_loudly():
    with pytest.raises(ValueError):
        wer("։", "anything")


class Echo:
    def transcribe(self, samples, language):
        return "բարև ես"


def test_evaluate_asr_reports_metrics():
    audio = np.zeros(16000 * 2, np.float32)
    r = evaluate_asr(Echo(), [Sample(audio, "բարև ես", "a"), Sample(audio, "բարև դու", "b")])
    assert r.wer == pytest.approx(0.25)
    assert r.rtf >= 0 and r.max_seconds >= 0
