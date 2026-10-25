from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    src_lang: str = "hy"
    tgt_lang: str = "en"
    asr_model: str = "models/asr-base"
    translation_model: str = "models/nllb-600m-ct2"
    translation_tokenizer: str = "models/nllb-600m-ct2"
    asr_compute_type: str = "int8"
    cpu_threads: int = 4
    # Segmentation
    vad_threshold: float = 0.5
    min_silence_s: float = 0.5
    min_speech_s: float = 0.25
    max_utterance_s: float = 6.0
    # Speaker identification (system audio only)
    speaker_threshold: float = 0.55
    min_embed_s: float = 1.0

    def asr_path(self) -> Path:
        return Path(self.asr_model)
