from __future__ import annotations

from pathlib import Path

import numpy as np

from meetai.languages import whisper_code


class FasterWhisperTranscriber:
    def __init__(self, model: str, compute_type: str = "int8", cpu_threads: int = 4) -> None:
        from faster_whisper import WhisperModel

        # A path means a local CTranslate2 model directory; fail loudly if it is missing.
        if "/" in model and not Path(model).is_dir():
            raise FileNotFoundError(
                f"ASR model directory {model!r} not found. Run scripts/convert_asr.sh first."
            )
        self._model = WhisperModel(
            model, device="cpu", compute_type=compute_type, cpu_threads=cpu_threads
        )

    def transcribe(self, samples: np.ndarray, language: str) -> str:
        segments, _ = self._model.transcribe(
            samples,
            language=whisper_code(language),
            beam_size=1,
            condition_on_previous_text=False,
            vad_filter=False,
        )
        return " ".join(s.text.strip() for s in segments).strip()
