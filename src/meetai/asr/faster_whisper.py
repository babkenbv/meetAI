from __future__ import annotations

from pathlib import Path

import numpy as np

from meetai.languages import whisper_code
from meetai.types import SAMPLE_RATE

# Short clips: the models sometimes invent ~10 words from a 1 s clip, which also costs ~3 s of decoding. Armenian speech
# needs ~14 tokens/s (max 19 on FLEURS), so cap the output at 22 tokens/s + 6. Applied to short clips only: capping all
# clips raised FLEURS WER from 33% to 46% (see DECISIONS.md).
SHORT_CLIP_S = 4.0
MAX_TOKENS_PER_SECOND = 22
MAX_TOKENS_SLACK = 6


class FasterWhisperTranscriber:
    def __init__(
        self, model: str, compute_type: str = "int8", cpu_threads: int = 4, initial_prompt: str | None = None
    ) -> None:
        from faster_whisper import WhisperModel

        # A path means a local CTranslate2 model directory; fail loudly if it is missing.
        if "/" in model and not Path(model).is_dir():
            raise FileNotFoundError(
                f"ASR model directory {model!r} not found. Run scripts/convert_asr.sh first."
            )
        self._initial_prompt = initial_prompt
        self._model = WhisperModel(
            model, device="cpu", compute_type=compute_type, cpu_threads=cpu_threads
        )

    def transcribe(self, samples: np.ndarray, language: str) -> str:
        seconds = len(samples) / SAMPLE_RATE
        limit = {"max_new_tokens": int(seconds * MAX_TOKENS_PER_SECOND) + MAX_TOKENS_SLACK} if seconds < SHORT_CLIP_S else {}
        segments, _ = self._model.transcribe(
            samples,
            language=whisper_code(language),
            beam_size=1,
            condition_on_previous_text=False,
            vad_filter=False,
            initial_prompt=self._initial_prompt,
            **limit,
        )
        return " ".join(s.text.strip() for s in segments).strip()
