"""Error-rate metrics and a small evaluation runner for ASR (and end-to-end) benchmarking."""

from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from meetai.types import SAMPLE_RATE


def normalize(text: str) -> str:
    """Lowercase, drop punctuation (including Armenian ։ ՝ ՞ ՜ ․ ՛), collapse whitespace."""
    text = unicodedata.normalize("NFC", text).lower()
    text = "".join(ch for ch in text if not unicodedata.category(ch).startswith("P"))
    text = re.sub(r"[՚-՟։]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def edit_distance(a: list, b: list) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def wer(reference: str, hypothesis: str) -> float:
    ref, hyp = normalize(reference).split(), normalize(hypothesis).split()
    if not ref:
        raise ValueError("Reference is empty after normalization")
    return edit_distance(ref, hyp) / len(ref)


def cer(reference: str, hypothesis: str) -> float:
    ref, hyp = list(normalize(reference).replace(" ", "")), list(normalize(hypothesis).replace(" ", ""))
    if not ref:
        raise ValueError("Reference is empty after normalization")
    return edit_distance(ref, hyp) / len(ref)


@dataclass(frozen=True)
class Sample:
    audio: np.ndarray  # 16 kHz mono float32
    reference: str
    name: str


def load_manifest(directory: str | Path) -> list[Sample]:
    """directory/manifest.tsv has `<file.wav>\\t<reference text>` per line; wavs must be 16 kHz mono."""
    import wave

    directory = Path(directory)
    samples = []
    for line in (directory / "manifest.tsv").read_text(encoding="utf-8").splitlines():
        name, reference = line.split("\t", 1)
        with wave.open(str(directory / name), "rb") as w:
            if w.getframerate() != SAMPLE_RATE or w.getnchannels() != 1 or w.getsampwidth() != 2:
                raise ValueError(f"{name}: expected 16 kHz mono 16-bit PCM")
            audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        samples.append(Sample(audio, reference, name))
    if not samples:
        raise ValueError(f"No samples in {directory}/manifest.tsv")
    return samples


@dataclass(frozen=True)
class AsrResult:
    wer: float
    cer: float
    rtf: float  # processing time / audio time; must stay well below 1 to keep up with live audio
    max_seconds: float  # slowest single utterance


def evaluate_asr(transcriber, samples: list[Sample], language: str = "hy") -> AsrResult:
    wers, cers, proc, dur, slowest = [], [], 0.0, 0.0, 0.0
    for s in samples:
        t0 = time.perf_counter()
        hyp = transcriber.transcribe(s.audio, language)
        elapsed = time.perf_counter() - t0
        wers.append(wer(s.reference, hyp))
        cers.append(cer(s.reference, hyp))
        proc, dur, slowest = proc + elapsed, dur + len(s.audio) / SAMPLE_RATE, max(slowest, elapsed)
    return AsrResult(float(np.mean(wers)), float(np.mean(cers)), proc / dur, slowest)
