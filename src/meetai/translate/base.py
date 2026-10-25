from __future__ import annotations

from typing import Protocol


class Translator(Protocol):
    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate `text` between ISO 639-1 languages."""
        ...
