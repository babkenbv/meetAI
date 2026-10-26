import numpy as np
import pytest

from meetai.audio.health import check_mic_signal


def test_healthy_noise_floor_passes():
    check_mic_signal(np.random.default_rng(0).normal(0, 0.03, 16000).astype(np.float32), "mic")


def test_dc_offset_fails_with_fix_hint():
    broken = np.full(16000, -0.38, np.float32) + np.random.default_rng(0).normal(0, 0.19, 16000).astype(np.float32)
    with pytest.raises(RuntimeError, match="pactl suspend-source"):
        check_mic_signal(broken, "alsa_input.test")


def test_saturated_signal_fails():
    with pytest.raises(RuntimeError, match="broken"):
        check_mic_signal(np.tile(np.array([0.6, -0.6], np.float32), 8000), "mic")


def test_empty_signal_fails():
    with pytest.raises(RuntimeError, match="no audio"):
        check_mic_signal(np.zeros(0, np.float32), "mic")
