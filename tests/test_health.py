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


def test_mostly_loud_noise_fails_with_hint():
    with pytest.raises(RuntimeError, match="unusable.*pactl suspend-source"):
        check_mic_signal(np.clip(noise(0.45, 48000), -1, 1), "alsa_input.test")


def test_mostly_clipped_signal_fails():
    with pytest.raises(RuntimeError, match="unusable"):
        check_mic_signal(np.clip(noise(2.0, 48000), -1, 1), "mic")


def test_intermittent_fault_with_mostly_clean_audio_passes():
    x = noise(0.03, 48000)
    x[:8000] = np.clip(noise(0.6, 8000), -1, 1)  # one bad window out of six
    check_mic_signal(x, "mic")


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


def test_session_start_warns_instead_of_raising_when_mic_check_is_ignored(monkeypatch, caplog):
    import logging
    import types

    from meetai import session as session_module

    def broken_probe(device, seconds=1.0, timeout=6.0):
        return np.clip(noise(0.45, 48000), -1, 1)

    monkeypatch.setattr(session_module, "probe_source", broken_probe)
    fake = types.SimpleNamespace(
        _mic="mic", _strict_mic_check=False, pipeline=types.SimpleNamespace(warm_up=lambda: None, start=lambda: None), _captures=[]
    )
    with caplog.at_level(logging.ERROR):
        session_module.Session.start(fake)
    assert "MIC PROBLEM" in caplog.text
    fake._strict_mic_check = True
    with pytest.raises(RuntimeError, match="unusable"):
        session_module.Session.start(fake)
