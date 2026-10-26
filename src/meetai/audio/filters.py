from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

from meetai.types import SAMPLE_RATE

HIGH_PASS_HZ = 100  # speech energy starts above ~100 Hz; the faulty mic input wandered below 2 Hz


class HighPass:
    """Streaming 2nd-order Butterworth high-pass. Removes DC offset and slow drift from one audio stream."""

    def __init__(self, cutoff_hz: float = HIGH_PASS_HZ) -> None:
        self._sos = butter(2, cutoff_hz, btype="highpass", fs=SAMPLE_RATE, output="sos")
        self._zi: np.ndarray | None = None

    def __call__(self, samples: np.ndarray) -> np.ndarray:
        if self._zi is None:
            # Start the filter as if the signal had always been at its first value: no start-up transient from the offset.
            self._zi = sosfilt_zi(self._sos) * samples[0]
        out, self._zi = sosfilt(self._sos, samples, zi=self._zi)
        return out.astype(np.float32)
