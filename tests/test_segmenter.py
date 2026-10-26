import numpy as np
import pytest

from meetai.audio.capture import CHUNK_SAMPLES
from meetai.types import SAMPLE_RATE, AudioChunk, Source
from meetai.vad import Segmenter

CHUNK_S = CHUNK_SAMPLES / SAMPLE_RATE


def run(segmenter, pattern):
    """pattern: string of 's' (speech) / '.' (silence) chunks. Returns emitted utterances."""
    out = []
    for i, c in enumerate(pattern):
        value = 1.0 if c == "s" else 0.0
        chunk = AudioChunk(Source.MIC, np.full(CHUNK_SAMPLES, value, np.float32), i * CHUNK_S)
        utt = segmenter.feed(chunk)
        if utt:
            out.append(utt)
    return out


def make(**kw):
    return Segmenter(Source.MIC, lambda x: float(x[0]), **kw)


def test_emits_after_min_silence():
    utts = run(make(min_silence_s=0.5), "." * 5 + "s" * 20 + "." * 30)
    assert len(utts) == 1
    assert utts[0].source is Source.MIC
    assert 0.6 < utts[0].t_end - utts[0].t_start < 1.8


def test_ignores_blips_shorter_than_min_speech():
    assert run(make(min_speech_s=0.25), "." * 5 + "s" * 3 + "." * 30) == []


def test_cuts_long_speech_at_max_utterance():
    utts = run(make(max_utterance_s=2.0), "s" * 200)
    assert len(utts) >= 2
    assert all(len(u.samples) <= 2.0 * SAMPLE_RATE + CHUNK_SAMPLES for u in utts)


def test_two_phrases_make_two_utterances():
    utts = run(make(), "s" * 20 + "." * 30 + "s" * 20 + "." * 30)
    assert len(utts) == 2
    assert utts[1].t_start > utts[0].t_end


def test_wrong_chunk_size_fails_loudly():
    import pytest

    with pytest.raises(ValueError):
        make().feed(AudioChunk(Source.MIC, np.zeros(100, np.float32), 0.0))


def test_pre_roll_keeps_audio_from_before_speech_onset():
    seg = make(min_silence_s=0.2, pad_chunks=10)
    (utt,) = run(seg, "." * 30 + "s" * 20 + "." * 30)
    # 10 pre-roll chunks + 20 speech chunks + at least the 6 chunks of trailing silence that end the utterance
    assert len(utt.samples) >= 36 * CHUNK_SAMPLES
    assert utt.t_start == pytest.approx((30 - 10) * CHUNK_S)
