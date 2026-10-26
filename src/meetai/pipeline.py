"""Wires capture -> segmentation -> speaker label -> ASR -> translation -> sinks."""

from __future__ import annotations

import logging
from pathlib import Path
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import numpy as np

from meetai.asr.base import Transcriber
from meetai.speakers import SpeakerLabeler
from meetai.text import clean_transcript
from meetai.translate.base import Translator
from meetai.types import SAMPLE_RATE, AudioChunk, Line, Source, Utterance
from meetai.vad import Segmenter

Sink = Callable[[Line], None]
log = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        segmenters: dict[Source, Segmenter],
        labeler: SpeakerLabeler,
        transcriber: Transcriber,
        translator: Translator,
        src_lang: str,
        tgt_lang: str,
        sinks: list[Sink],
        clock: Callable[[], float] | None = None,
        utterance_dir: str | None = None,
    ) -> None:
        self._segmenters = segmenters
        self._labeler = labeler
        self._transcriber = transcriber
        self._translator = translator
        self._src, self._tgt = src_lang, tgt_lang
        self._sinks = sinks
        self._utterance_dir = Path(utterance_dir) if utterance_dir else None
        if self._utterance_dir:
            self._utterance_dir.mkdir(parents=True, exist_ok=True)
        t0 = time.monotonic()
        self.clock = clock or (lambda: time.monotonic() - t0)
        self._queue: queue.Queue[Utterance | None] = queue.Queue()
        self._worker = threading.Thread(target=self._work, name="pipeline-worker", daemon=True)
        self._error: BaseException | None = None
        self._label_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="speaker-label")

    def warm_up(self) -> None:
        """Run each model once so the first real utterance does not pay one-time initialisation costs."""
        noise = np.random.default_rng(0).standard_normal(SAMPLE_RATE * 2).astype(np.float32) * 0.01
        self._labeler.label(Utterance(Source.SYSTEM, noise, 0.0, 2.0))
        self._transcriber.transcribe(noise, self._src)
        self._translator.translate("բարև", self._src, self._tgt)

    def start(self) -> None:
        self._worker.start()

    def stop(self) -> None:
        self._queue.put(None)
        self._worker.join(timeout=5)
        self._label_pool.shutdown(wait=False)

    def fail(self, exc: BaseException) -> None:
        """Called from any thread; the first error is kept and re-raised by `check`."""
        if self._error is None:
            self._error = exc

    def check(self) -> None:
        if self._error is not None:
            raise self._error

    def feed(self, chunk: AudioChunk) -> None:
        utt = self._segmenters[chunk.source].feed(chunk)
        if utt is not None:
            log.info("%s utterance %.1fs queued (backlog %d)", utt.source.value, len(utt.samples) / SAMPLE_RATE, self._queue.qsize())
            self._queue.put(utt)

    def _work(self) -> None:
        while True:
            utt = self._queue.get()
            if utt is None:
                return
            try:
                self._process(utt)
            except BaseException as exc:
                self.fail(exc)
                return

    def _process(self, utt: Utterance) -> None:
        # Speaker embedding runs in parallel with ASR; it is independent of the text.
        speaker_future = self._label_pool.submit(self._labeler.label, utt)
        text = clean_transcript(self._transcriber.transcribe(utt.samples, self._src))
        speaker = speaker_future.result()
        if not text:
            log.info("%s utterance at %.1fs: empty transcript, dropped", utt.source.value, utt.t_start)
            return
        english = self._translator.translate(text, self._src, self._tgt)
        line = Line(
            t_start=utt.t_start,
            t_end=utt.t_end,
            source=utt.source,
            speaker=speaker,
            src_lang=self._src,
            src_text=text,
            tgt_lang=self._tgt,
            tgt_text=english,
            latency_s=self.clock() - utt.t_end,
        )
        if self._utterance_dir:
            self._save(utt, line)
        for sink in self._sinks:
            sink(line)

    def _save(self, utt: Utterance, line: Line) -> None:
        """Debug aid: keep the audio and transcript of each utterance for offline model comparison."""
        import soundfile as sf

        name = f"{int(utt.t_start * 1000):08d}_{utt.source.value}.wav"
        sf.write(self._utterance_dir / name, utt.samples, SAMPLE_RATE, subtype="PCM_16")
        with open(self._utterance_dir / "transcripts.tsv", "a", encoding="utf-8") as f:
            f.write(f"{name}\t{line.src_text}\t{line.tgt_text}\n")
