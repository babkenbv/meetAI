from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

SAMPLE_RATE = 16_000


class Source(str, Enum):
    MIC = "mic"
    SYSTEM = "system"


@dataclass(frozen=True)
class AudioChunk:
    """Mono float32 audio at SAMPLE_RATE. t_start is seconds since the session started."""

    source: Source
    samples: np.ndarray
    t_start: float


@dataclass(frozen=True)
class Utterance:
    """A finished stretch of speech from one source."""

    source: Source
    samples: np.ndarray
    t_start: float
    t_end: float


@dataclass(frozen=True)
class Line:
    """One transcribed and translated utterance, ready for display or storage."""

    t_start: float
    t_end: float
    source: Source
    speaker: str
    src_lang: str
    src_text: str
    tgt_lang: str
    tgt_text: str
    latency_s: float
