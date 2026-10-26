import numpy as np
import pytest

from meetai.audio.filters import HighPass
from meetai.audio.health import check_mic_signal


def noise(std, n=16000, seed=0):
    return np.random.default_rng(seed).normal(0, std, n).astype(np.float32)


def test_healthy_noise_floor_passes():
    check_mic_signal(noise(0.03), "mic")


def test_dc_offset_alone_is_tolerated_because_the_pipeline_filters_it():
    check_mic_signal(np.full(16000, -0.38, np.float32) + noise(0.02), "mic")


def test_loud_noise_fails_with_hint():
    with pytest.raises(RuntimeError, match="unusable.*pactl suspend-source"):
        check_mic_signal(np.clip(noise(0.45), -1, 1), "alsa_input.test")


def test_clipping_fails():
    with pytest.raises(RuntimeError, match="clipped"):
        check_mic_signal(np.tile(np.array([1.0, -1.0], np.float32), 8000) * 0.02 + np.where(np.arange(16000) % 20 == 0, 1.0, 0.0), "mic")


def test_empty_signal_fails():
    with pytest.raises(RuntimeError, match="no audio"):
        check_mic_signal(np.zeros(0, np.float32), "mic")


def test_high_pass_removes_offset_and_keeps_speech_band():
    t = np.arange(16000 * 2) / 16000
    speech_like = 0.2 * np.sin(2 * np.pi * 500 * t).astype(np.float32)
    out = HighPass()(speech_like - 0.4)
    tail = out[8000:]
    assert abs(tail.mean()) < 0.01
    assert np.sqrt((tail**2).mean()) == pytest.approx(0.2 / np.sqrt(2), rel=0.05)
