import numpy as np

from meetai.speakers import OnlineSpeakerClusterer, SpeakerLabeler
from meetai.types import SAMPLE_RATE, Source, Utterance


def vec(i, noise=0.0, seed=0, dim=8):
    v = np.zeros(dim, np.float32)
    v[i] = 1.0
    return v + noise * np.random.default_rng(seed).standard_normal(dim).astype(np.float32)


def test_same_speaker_keeps_label_and_new_speaker_gets_new_label():
    c = OnlineSpeakerClusterer(threshold=0.6)
    assert c.assign(vec(0)) == "Speaker 1"
    assert c.assign(vec(1)) == "Speaker 2"
    assert c.assign(vec(0, 0.1, 1)) == "Speaker 1"
    assert c.assign(vec(1, 0.1, 2)) == "Speaker 2"
    assert c.assign(vec(2)) == "Speaker 3"


def test_short_clip_inherits_previous_label():
    c = OnlineSpeakerClusterer()
    assert c.assign_short() == "Speaker 1"
    c.assign(vec(0))
    c.assign(vec(1))
    assert c.assign_short() == "Speaker 2"


class FakeEmbedder:
    def __init__(self, vectors):
        self.vectors = list(vectors)

    def embed(self, samples):
        return self.vectors.pop(0)


def utt(source, seconds):
    return Utterance(source, np.zeros(int(seconds * SAMPLE_RATE), np.float32), 0.0, seconds)


def test_mic_is_always_me_and_does_not_touch_clusters():
    labeler = SpeakerLabeler(FakeEmbedder([]), OnlineSpeakerClusterer())
    assert labeler.label(utt(Source.MIC, 2.0)) == "Me"


def test_system_utterances_are_clustered():
    labeler = SpeakerLabeler(FakeEmbedder([vec(0), vec(1), vec(0, 0.05, 3)]), OnlineSpeakerClusterer(0.6))
    labels = [labeler.label(utt(Source.SYSTEM, 2.0)) for _ in range(3)]
    assert labels == ["Speaker 1", "Speaker 2", "Speaker 1"]
