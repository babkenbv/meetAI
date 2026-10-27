from __future__ import annotations

from typing import Protocol

from meetai.translate.base import TranslationResult, Translator


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
        return self.translate_result(text, src_lang, tgt_lang).text

    def translate_result(self, text: str, src_lang: str, tgt_lang: str) -> TranslationResult:
        if len(text.split()) <= self._max_words:
            out, confidence = self._short.translate_scored(text, src_lang, tgt_lang)
            if confidence >= self._min_confidence:
                return TranslationResult(out, True)
        return self._long.translate_result(text, src_lang, tgt_lang)
