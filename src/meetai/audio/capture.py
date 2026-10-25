"""Capture one audio source as 16 kHz mono float32 using `parec` (PulseAudio/PipeWire)."""

from __future__ import annotations

import subprocess
import threading
import time
from typing import Callable

import numpy as np

from meetai.types import SAMPLE_RATE, AudioChunk, Source

CHUNK_SAMPLES = 512  # 32 ms; also the Silero VAD window size at 16 kHz
BYTES_PER_SAMPLE = 4


class Capture:
    """Reads one source in a thread and calls `on_chunk` with fixed-size chunks.

    `clock` returns seconds since session start, so mic and system chunks share a timeline.
    """

    def __init__(
        self,
        source: Source,
        device: str,
        on_chunk: Callable[[AudioChunk], None],
        clock: Callable[[], float],
        on_error: Callable[[BaseException], None],
    ) -> None:
        self.source = source
        self.device = device
        self._on_chunk = on_chunk
        self._clock = clock
        self._on_error = on_error
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._stopping = threading.Event()

    def start(self) -> None:
        self._proc = subprocess.Popen(
            [
                "parec",
                f"--device={self.device}",
                "--format=float32le",
                f"--rate={SAMPLE_RATE}",
                "--channels=1",
                "--latency-msec=32",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(0.2)
        if self._proc.poll() is not None:
            err = self._proc.stderr.read().decode(errors="replace").strip()
            raise RuntimeError(f"parec failed for {self.device!r}: {err}")
        self._thread = threading.Thread(target=self._run, name=f"capture-{self.source.value}", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            self._read_loop()
        except BaseException as exc:  # reported to the owner, which stops the session
            self._on_error(exc)

    def _read_loop(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        size = CHUNK_SAMPLES * BYTES_PER_SAMPLE
        while not self._stopping.is_set():
            buf = self._proc.stdout.read(size)
            if len(buf) < size:
                if self._stopping.is_set():
                    return
                err = self._proc.stderr.read().decode(errors="replace").strip()
                raise RuntimeError(f"Audio stream for {self.device!r} ended unexpectedly: {err}")
            samples = np.frombuffer(buf, dtype=np.float32).copy()
            self._on_chunk(AudioChunk(self.source, samples, self._clock() - CHUNK_SAMPLES / SAMPLE_RATE))

    def stop(self) -> None:
        self._stopping.set()
        if self._proc is not None:
            self._proc.terminate()
            self._proc.wait(timeout=2)
        if self._thread is not None:
            self._thread.join(timeout=2)
