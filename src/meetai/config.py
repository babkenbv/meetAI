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
    # One-word inputs go to this model when it is confident (greetings); everything else to the NLLB model above.
    translation_short_model: str | None = "models/opus-hy-en-ct2"
    translation_min_confidence: float = -0.9  # NLLB below this is shown as [unsure]
    short_max_words: int = 1
    short_min_confidence: float = -1.5
    # Accurate model: used only for short utterances while nothing is queued (its cost is ~2.7 s even for 1 s of audio).
    asr_accurate_model: str | None = "models/asr"
    asr_accurate_max_s: float = 2.0
    # Prompt priming for the accurate model only: it heard "Ողջույն" as "Ողջուհին" without it, and WER on 7 read sentences
    # (none containing these words) fell from 45.1% to 37.8%. It hurt the base model on FLEURS (29.8% -> 34.8%).
    asr_accurate_prompt: str | None = "Բարև, ողջույն, շնորհակալություն, ինչպես ես, ինչպես եք, լավ եմ։"
    asr_compute_type: str = "int8"
    cpu_threads: int = 4
    # Segmentation
    vad_threshold: float = 0.5
    min_silence_s: float = 0.5
    min_speech_s: float = 0.25
    max_utterance_s: float = 6.0
    # Audio kept from before the detector fired: it needs ~100 ms of speech to trigger, so with 0.13 s the first sound of a
    # word was clipped in 2 of 5 of the user's one-word clips (loud at t=0). Whisper models mishear clipped onsets.
    pre_roll_s: float = 0.3
    # Speaker identification (system audio only)
    speaker_threshold: float = 0.4
    min_embed_s: float = 1.0

    def asr_path(self) -> Path:
        return Path(self.asr_model)
