"""Builds the real models and runs a live session. Shared by the CLI and the server."""

from __future__ import annotations

from meetai.asr.faster_whisper import FasterWhisperTranscriber
from meetai.audio.capture import Capture
from meetai.config import Config
from meetai.pipeline import Pipeline, Sink
from meetai.speakers import OnlineSpeakerClusterer, SpeakerLabeler, SpeechBrainEmbedder
from meetai.translate.nllb_ct2 import NllbTranslator
from meetai.types import Source
from meetai.vad import Segmenter, load_silero


class Session:
    def __init__(self, cfg: Config, mic: str, system: str, sinks: list[Sink]) -> None:
        # Silero VAD keeps internal state, so each source gets its own model instance.
        segmenters = {
            src: Segmenter(
                src,
                load_silero(),
                cfg.vad_threshold,
                cfg.min_silence_s,
                cfg.min_speech_s,
                cfg.max_utterance_s,
            )
            for src in Source
        }
        labeler = SpeakerLabeler(
            SpeechBrainEmbedder(),
            OnlineSpeakerClusterer(cfg.speaker_threshold, cfg.min_embed_s),
        )
        self.pipeline = Pipeline(
            segmenters,
            labeler,
            FasterWhisperTranscriber(cfg.asr_model, cfg.asr_compute_type, cfg.cpu_threads),
            NllbTranslator(cfg.translation_model, cfg.translation_tokenizer, cfg.cpu_threads),
            cfg.src_lang,
            cfg.tgt_lang,
            sinks,
        )
        self._captures = [
            Capture(Source.MIC, mic, self.pipeline.feed, self.pipeline.clock, self.pipeline.fail),
            Capture(Source.SYSTEM, system, self.pipeline.feed, self.pipeline.clock, self.pipeline.fail),
        ]

    def start(self) -> None:
        self.pipeline.warm_up()
        self.pipeline.start()
        for c in self._captures:
            c.start()

    def check(self) -> None:
        self.pipeline.check()

    def stop(self) -> None:
        for c in self._captures:
            c.stop()
        self.pipeline.stop()
