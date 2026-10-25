from __future__ import annotations

from typing import Protocol

import numpy as np


class Transcriber(Protocol):
    """Speech to text. Swap implementations (local model, private deployment, managed inference) here."""

    def transcribe(self, samples: np.ndarray, language: str) -> str:
        """16 kHz mono float32 audio -> text in `language` (ISO 639-1). Empty string if no speech."""
        ...
