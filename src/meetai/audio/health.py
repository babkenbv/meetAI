"""Startup check that a microphone delivers a plausible signal instead of silence, a DC offset or saturation."""

from __future__ import annotations

import os
import select
import subprocess
import time

import numpy as np

from meetai.audio.filters import HighPass
from meetai.types import SAMPLE_RATE

MAX_NOISE_RMS = 0.3  # after high-pass filtering: speech is ~0.1 to 0.3 and noise should be far lower; the faulty state measured 0.3 to 0.4
MAX_CLIPPED_FRACTION = 0.01  # samples at full scale; a healthy mic essentially never clips


WINDOW_S = 0.5
MAX_BAD_WINDOW_FRACTION = 0.5  # the faulty input alternates between clean and unusable moments; fail only if mostly unusable


def check_mic_signal(samples: np.ndarray, device: str) -> None:
    """Raises RuntimeError if the signal is silent, or mostly saturated or drowned in noise (speech cannot be detected).

    The slow drift / DC offset of the faulty input is removed by the same high-pass the pipeline uses, so it does not
    count here. Judged in short windows because the fault comes and goes within a second.
    """
    if len(samples) == 0:
        raise RuntimeError(f"Microphone {device!r} delivered no audio")
    filtered = HighPass()(samples)
    size = int(WINDOW_S * SAMPLE_RATE)
    # Clipping is judged on the raw samples, noise on the filtered ones.
    windows = [(filtered[i : i + size], samples[i : i + size]) for i in range(0, len(samples) - size + 1, size)]
    bad = sum(
        1
        for f, raw in windows
        if float(np.sqrt((f**2).mean())) > MAX_NOISE_RMS or float((np.abs(raw) >= 0.999).mean()) > MAX_CLIPPED_FRACTION
    )
    if windows and bad / len(windows) > MAX_BAD_WINDOW_FRACTION:
        raise RuntimeError(
            f"Microphone {device!r} signal is unusable: {bad} of {len(windows)} half-second windows were saturated or "
            "drowned in noise. Speech cannot be detected. Check for loud noise near the mic or a faulty/loose headset plug, "
            f"try a headset, or re-open the device: pactl suspend-source {device} 1; pactl suspend-source {device} 0."
        )


def probe_source(device: str, seconds: float = 1.0, timeout: float = 6.0) -> np.ndarray:
    """Capture `seconds` of audio. Waits for the samples, not for a fixed time: parec takes a moment to start delivering."""
    wanted = int(seconds * SAMPLE_RATE) * 4
    proc = subprocess.Popen(
        ["parec", f"--device={device}", "--format=float32le", f"--rate={SAMPLE_RATE}", "--channels=1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    data, deadline = b"", time.time() + timeout
    try:
        while len(data) < wanted and time.time() < deadline:
            ready, _, _ = select.select([proc.stdout], [], [], 0.2)
            if ready:
                data += os.read(proc.stdout.fileno(), 65536)
    finally:
        proc.terminate()
    return np.frombuffer(data[: len(data) // 4 * 4], dtype=np.float32)
