import numpy as np

from meetai.audio.capture import CHUNK_SAMPLES
from meetai.format import format_clock, format_line
from meetai.pipeline import Pipeline
from meetai.speakers import OnlineSpeakerClusterer, SpeakerLabeler
from meetai.types import SAMPLE_RATE, AudioChunk, Line, Source, Utterance
from meetai.vad import Segmenter


# Speech stand-in: alternating samples (Nyquist frequency) pass the pipeline's high-pass, unlike a constant offset.
ALT = np.tile(np.array([1.0, -1.0], np.float32), CHUNK_SAMPLES // 2)


def loudness(chunk):
    return float(np.abs(chunk).mean())


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
    segs = {s: Segmenter(s, loudness, min_silence_s=0.2) for s in Source}
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
            p.feed(AudioChunk(source, v * ALT, t))
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

    segs = {s: Segmenter(s, loudness, min_silence_s=0.2) for s in Source}
    p = Pipeline(segs, SpeakerLabeler(FakeEmbedder(), OnlineSpeakerClusterer()), Boom(), FakeMt(), "hy", "en", [])
    p.start()
    for i, v in enumerate([1.0] * 40 + [0.0] * 20):
        p.feed(AudioChunk(Source.MIC, v * ALT, i * 0.032))
    p.stop()
    with pytest.raises(RuntimeError, match="model exploded"):
        p.check()


class NamedAsr:
    def __init__(self, name):
        self.name = name

    def transcribe(self, samples, language):
        return self.name


def _run(duration_s, accurate=True, preload_queue=False):
    lines = []
    seg = {s: Segmenter(s, lambda x: 0.0) for s in Source}
    p = Pipeline(
        seg,
        SpeakerLabeler(FakeEmbedder(), OnlineSpeakerClusterer()),
        NamedAsr("fast"),
        FakeMt(),
        "hy",
        "en",
        [lines.append],
        accurate_transcriber=NamedAsr("accurate") if accurate else None,
        accurate_max_s=3.0,
    )
    if preload_queue:
        p._queue.put(object())
    utt = Utterance(Source.SYSTEM, np.zeros(int(duration_s * SAMPLE_RATE), np.float32), 0.0, duration_s)
    p._process(utt)
    return lines[0].src_text


def test_short_idle_utterance_uses_accurate_model():
    assert _run(1.5) == "accurate"


def test_long_utterance_uses_fast_model():
    assert _run(5.0) == "fast"


def test_backlog_forces_fast_model():
    assert _run(1.5, preload_queue=True) == "fast"


def test_without_accurate_model_always_fast():
    assert _run(1.5, accurate=False) == "fast"


def test_slow_accurate_path_pauses_accurate_model_then_retries():
    now = [0.0]

    class SlowAccurate:
        def transcribe(self, samples, language):
            now[0] += 5.0  # slower than the budget
            return "accurate"

    lines = []
    seg = {s: Segmenter(s, lambda x: 0.0) for s in Source}
    p = Pipeline(
        seg, SpeakerLabeler(FakeEmbedder(), OnlineSpeakerClusterer()), NamedAsr("fast"), FakeMt(), "hy", "en",
        [lines.append], clock=lambda: now[0], accurate_transcriber=SlowAccurate(), accurate_max_s=3.0,
    )
    utt = Utterance(Source.SYSTEM, np.zeros(SAMPLE_RATE, np.float32), 0.0, 1.0)
    p._process(utt)
    p._process(utt)  # still inside the pause
    now[0] += 31.0
    p._process(utt)  # pause over: the accurate model is tried again
    assert [l.src_text for l in lines] == ["accurate", "fast", "accurate"]
