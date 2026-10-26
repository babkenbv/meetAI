from __future__ import annotations

from typing import Protocol

from meetai.translate.base import Translator


class ScoredTranslator(Protocol):
    def translate_scored(self, text: str, src_lang: str, tgt_lang: str) -> tuple[str, float]: ...


class ShortPhraseTranslator:
    """Very short inputs go to `short` if it is confident, otherwise (and for everything longer) to `long`.

    Measured on 26 everyday phrases (see DECISIONS.md): NLLB-600M mistranslates greetings (Բարև -> "What's going on?")
    while OPUS-MT hy-en gets them right, but OPUS-MT produces junk ("TEPA") when unsure and is poor on anything
    longer. OPUS's own mean token log-probability separates most of that junk, so it is used as the gate.
    """

    def __init__(self, short: ScoredTranslator, long: Translator, max_words: int = 1, min_confidence: float = -1.5) -> None:
        self._short = short
        self._long = long
        self._max_words = max_words
        self._min_confidence = min_confidence

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        if len(text.split()) <= self._max_words:
            out, confidence = self._short.translate_scored(text, src_lang, tgt_lang)
            if confidence >= self._min_confidence:
                return out
        return self._long.translate(text, src_lang, tgt_lang)
