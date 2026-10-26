from __future__ import annotations

from meetai.translate.base import Translator


class ShortPhraseTranslator:
    """Sends very short inputs to `short` and everything else to `long`.

    Measured: NLLB-600M is much better on sentences but guesses on one-word greetings (Բարև -> "What's going on?"),
    while OPUS-MT hy-en handles greetings well and is poor on sentences (BLEU 20.7 vs 39.7). See DECISIONS.md.
    """

    def __init__(self, short: Translator, long: Translator, max_words: int = 2) -> None:
        self._short = short
        self._long = long
        self._max_words = max_words

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        words = len(text.split())
        return (self._short if words <= self._max_words else self._long).translate(text, src_lang, tgt_lang)
