import numpy as np

from meetai.audio.capture import CHUNK_SAMPLES
from meetai.format import format_clock, format_line
from meetai.pipeline import Pipeline
from meetai.speakers import OnlineSpeakerClusterer, SpeakerLabeler
from meetai.types import SAMPLE_RATE, AudioChunk, Line, Source, Utterance
from meetai.vad import Segmenter


class FakeAsr:
    def transcribe(self, samples, language):
        return "Բարև" if len(samples) else ""


class FakeMt:
    def translate(self, text, src_lang, tgt_lang):
        return "Hello"


class FakeEmbedder:
    def embed(self, samples):
        return np.array([1.0, 0.0], np.float32)


def test_format_line_has_time_speaker_original_and_translation():
    line = Line(72.4, 74.0, Source.SYSTEM, "Speaker 1", "hy", "Բարև", "en", "Hello", 1.2)
    assert format_line(line).startswith("[00:01:12] Speaker 1")
    assert "HY: Բարև" in format_line(line)
    assert "EN: Hello" in format_line(line)
    assert format_line(line, show_latency=True).endswith("(1.2s)")
    assert format_clock(3725) == "01:02:05"


def test_pipeline_end_to_end_with_fakes():
    lines = []
    segs = {s: Segmenter(s, lambda x: float(x[0]), min_silence_s=0.2) for s in Source}
    p = Pipeline(
        segs,
        SpeakerLabeler(FakeEmbedder(), OnlineSpeakerClusterer()),
        FakeAsr(),
        FakeMt(),
        "hy",
        "en",
        [lines.append],
        clock=lambda: 10.0,
    )
    p.start()
    t = 0.0
    for source in (Source.MIC, Source.SYSTEM):
        for v in [1.0] * 40 + [0.0] * 20:
            p.feed(AudioChunk(source, np.full(CHUNK_SAMPLES, v, np.float32), t))
            t += CHUNK_SAMPLES / SAMPLE_RATE
    p.stop()
    p.check()
    assert [l.speaker for l in lines] == ["Me", "Speaker 1"]
    assert all(l.src_text == "Բարև" and l.tgt_text == "Hello" for l in lines)


def test_worker_error_is_raised_by_check():
    import pytest

    class Boom:
        def transcribe(self, samples, language):
            raise RuntimeError("model exploded")

    segs = {s: Segmenter(s, lambda x: float(x[0]), min_silence_s=0.2) for s in Source}
    p = Pipeline(segs, SpeakerLabeler(FakeEmbedder(), OnlineSpeakerClusterer()), Boom(), FakeMt(), "hy", "en", [])
    p.start()
    for i, v in enumerate([1.0] * 40 + [0.0] * 20):
        p.feed(AudioChunk(Source.MIC, np.full(CHUNK_SAMPLES, v, np.float32), i * 0.032))
    p.stop()
    with pytest.raises(RuntimeError, match="model exploded"):
        p.check()
