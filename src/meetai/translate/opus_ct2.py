from __future__ import annotations

from pathlib import Path

from meetai.translate.base import TranslationResult


class OpusHyEnTranslator:
    """Helsinki-NLP/opus-mt-hy-en (Marian) converted to CTranslate2 int8. Armenian to English only."""

    def __init__(self, model_dir: str, cpu_threads: int = 4, beam_size: int = 4) -> None:
        import ctranslate2
        from transformers import AutoTokenizer

        if not Path(model_dir).is_dir():
            raise FileNotFoundError(f"Translation model directory {model_dir!r} not found. Run scripts/convert_opus.sh first.")
        self._translator = ctranslate2.Translator(model_dir, device="cpu", compute_type="int8", intra_threads=cpu_threads)
        self._tok = AutoTokenizer.from_pretrained(model_dir)
        self._beam_size = beam_size

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        return self.translate_scored(text, src_lang, tgt_lang)[0]

    def translate_result(self, text: str, src_lang: str, tgt_lang: str) -> TranslationResult:
        out, confidence = self.translate_scored(text, src_lang, tgt_lang)
        return TranslationResult(out, confidence >= -1.5)

    def translate_scored(self, text: str, src_lang: str, tgt_lang: str) -> tuple[str, float]:
        """Returns (translation, confidence). Confidence is the mean token log-probability: 0 is certain, lower is less sure."""
        if (src_lang, tgt_lang) != ("hy", "en"):
            raise ValueError(f"opus-mt-hy-en only translates hy -> en, not {src_lang} -> {tgt_lang}")
        if not text.strip():
            return "", 0.0
        tokens = self._tok.convert_ids_to_tokens(self._tok.encode(text))
        result = self._translator.translate_batch(
            [tokens], beam_size=self._beam_size, max_decoding_length=100, return_scores=True
        )[0]
        out = self._tok.decode(self._tok.convert_tokens_to_ids(result.hypotheses[0]), skip_special_tokens=True)
        return out.strip(), float(result.scores[0])
