from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TranslationResult:
    text: str
    confident: bool  # False when the model is guessing (e.g. translating ASR gibberish); shown to the user as [unsure]


class Translator(Protocol):
    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate `text` between ISO 639-1 languages."""
        ...

    def translate_result(self, text: str, src_lang: str, tgt_lang: str) -> TranslationResult:
        """Like `translate`, but also says whether the model was confident."""
        ...
