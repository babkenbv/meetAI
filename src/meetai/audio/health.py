"""Startup check that a microphone delivers a plausible signal instead of silence, a DC offset or saturation."""

from __future__ import annotations

import os
import select
import subprocess
import time

import numpy as np

from meetai.types import SAMPLE_RATE

MAX_DC_OFFSET = 0.1  # a healthy mic is centred on 0; the broken state seen was -0.38 with 0.19 of slow swing
MAX_STEADY_RMS = 0.4  # loud close speech reaches ~0.3; the broken state measured 0.49 steady


def check_mic_signal(samples: np.ndarray, device: str) -> None:
    """Raises RuntimeError with a fix hint if the signal looks like a stuck or saturated input."""
    if len(samples) == 0:
        raise RuntimeError(f"Microphone {device!r} delivered no audio")
    dc = float(samples.mean())
    rms = float(np.sqrt((samples**2).mean()))
    if abs(dc) > MAX_DC_OFFSET or rms > MAX_STEADY_RMS:
        raise RuntimeError(
            f"Microphone {device!r} signal is broken (DC offset {dc:+.2f}, rms {rms:.2f}). Speech cannot be detected. "
            f"Re-open the device: pactl suspend-source {device} 1; pactl suspend-source {device} 0. "
            "If it persists, lower the input volume or check the headset plug."
        )


def probe_source(device: str, seconds: float = 1.0) -> np.ndarray:
    proc = subprocess.Popen(
        ["parec", f"--device={device}", "--format=float32le", f"--rate={SAMPLE_RATE}", "--channels=1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    data, deadline = b"", time.time() + seconds
    try:
        while time.time() < deadline:
            ready, _, _ = select.select([proc.stdout], [], [], 0.2)
            if ready:
                data += os.read(proc.stdout.fileno(), 65536)
    finally:
        proc.terminate()
    return np.frombuffer(data[: len(data) // 4 * 4], dtype=np.float32)
