"""Speech segmentation: turns a stream of 32 ms chunks into finished utterances."""

from __future__ import annotations

from typing import Callable

import numpy as np

from meetai.audio.capture import CHUNK_SAMPLES
from meetai.types import SAMPLE_RATE, AudioChunk, Source, Utterance

SpeechProb = Callable[[np.ndarray], float]


def load_silero() -> SpeechProb:
    """Returns a function mapping one 512-sample chunk to a speech probability (Silero VAD, ONNX)."""
    import torch
    from silero_vad import load_silero_vad

    model = load_silero_vad(onnx=True)

    def prob(chunk: np.ndarray) -> float:
        return float(model(torch.from_numpy(chunk), SAMPLE_RATE).item())

    return prob


class Segmenter:
    """One instance per source (VAD state is per stream).

    An utterance ends after `min_silence_s` of silence, or is cut at `max_utterance_s`
    so that latency stays bounded during long monologues.
    """

    def __init__(
        self,
        source: Source,
        speech_prob: SpeechProb,
        threshold: float = 0.5,
        min_silence_s: float = 0.5,
        min_speech_s: float = 0.25,
        max_utterance_s: float = 8.0,
        pad_chunks: int = 4,
    ) -> None:
        self.source = source
        self._prob = speech_prob
        self._threshold = threshold
        self._min_silence = int(min_silence_s * SAMPLE_RATE / CHUNK_SAMPLES)
        self._min_speech = int(min_speech_s * SAMPLE_RATE / CHUNK_SAMPLES)
        self._max_chunks = int(max_utterance_s * SAMPLE_RATE / CHUNK_SAMPLES)
        self._pad = pad_chunks
        self._pre: list[np.ndarray] = []  # recent non-speech chunks kept as leading padding
        self._buf: list[np.ndarray] = []
        self._t_start = 0.0
        self._silence = 0
        self._speech = 0

    def feed(self, chunk: AudioChunk) -> Utterance | None:
        if len(chunk.samples) != CHUNK_SAMPLES:
            raise ValueError(f"Expected {CHUNK_SAMPLES} samples, got {len(chunk.samples)}")
        is_speech = self._prob(chunk.samples) >= self._threshold

        if not self._buf:
            if not is_speech:
                self._pre.append(chunk.samples)
                self._pre = self._pre[-self._pad :]
                return None
            self._buf = [*self._pre, chunk.samples]
            self._t_start = chunk.t_start - len(self._pre) * CHUNK_SAMPLES / SAMPLE_RATE
            self._pre = []
            self._silence = 0
            self._speech = 1
            return None

        self._buf.append(chunk.samples)
        if is_speech:
            self._silence = 0
            self._speech += 1
        else:
            self._silence += 1

        if self._silence >= self._min_silence or len(self._buf) >= self._max_chunks:
            return self._finish(chunk.t_start + CHUNK_SAMPLES / SAMPLE_RATE)
        return None

    def _finish(self, t_end: float) -> Utterance | None:
        enough_speech = self._speech >= self._min_speech
        samples = np.concatenate(self._buf)
        t_start = self._t_start
        self._buf, self._silence, self._speech = [], 0, 0
        if not enough_speech:
            return None
        return Utterance(self.source, samples, t_start, t_end)
