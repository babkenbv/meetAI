# Test checklist (derived from the brief)

Automated (`PYTHONPATH=src .venv/bin/python -m pytest`): segmentation, speaker clustering, `Me` for mic,
pipeline wiring with fakes, error propagation, line format, device parsing, server API.

Manual / live (run before the interview):
- [ ] `meetai --list-devices` shows a microphone and a monitor source; `--mic` / `--system` override defaults.
- [ ] Output is not muted (`pactl list sinks | grep Mute`), otherwise the monitor is silent.
- [ ] Mic and system audio are captured at the same time (speak while a video plays).
- [ ] Mic speech is always labelled `Me`.
- [ ] Two different voices on system audio get `Speaker 1` / `Speaker 2`; each keeps its label for the session.
- [ ] Every line shows time, speaker, HY original and EN translation.
- [ ] End of phrase to EN line is at most 5 s (`--show-latency`), including during a long monologue.
- [ ] Runs with the network disabled (no cloud calls).
- [ ] A missing model directory or audio device stops the program with a clear error.
- [ ] `git status` shows no weights, audio files or keys.
- [ ] Web: start/stop works, lines stream in, an induced error shows in the red banner.
