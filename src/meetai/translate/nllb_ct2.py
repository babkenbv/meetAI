from __future__ import annotations

from pathlib import Path

from meetai.languages import nllb_code
from meetai.translate.base import TranslationResult


class NllbTranslator:
    """NLLB-200 distilled 600M converted to CTranslate2 (int8), run on CPU."""

    def __init__(
        self, model_dir: str, tokenizer: str, cpu_threads: int = 4, beam_size: int = 4, min_confidence: float = -0.9
    ) -> None:
        import ctranslate2

        if not Path(model_dir).is_dir():
            raise FileNotFoundError(
                f"Translation model directory {model_dir!r} not found. Run scripts/convert_nllb.sh first."
            )
        self._translator = ctranslate2.Translator(
            model_dir, device="cpu", compute_type="int8", intra_threads=cpu_threads
        )
        self._tokenizer_name = tokenizer
        self._beam_size = beam_size
        self._min_confidence = min_confidence
        self._tokenizers: dict[str, object] = {}

    def _tok(self, src_lang: str):
        if src_lang not in self._tokenizers:
            from transformers import AutoTokenizer

            self._tokenizers[src_lang] = AutoTokenizer.from_pretrained(
                self._tokenizer_name, src_lang=nllb_code(src_lang)
            )
        return self._tokenizers[src_lang]

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        return self.translate_result(text, src_lang, tgt_lang).text

    def translate_result(self, text: str, src_lang: str, tgt_lang: str) -> TranslationResult:
        """Confidence is the mean token log-probability of the output; below `min_confidence` it is a guess.

        Measured: real Armenian sentences average -0.46 (p10 -0.64); gibberish from the ASR averages -1.08, and NLLB
        then invents stock sentences such as "What is the meaning of life?". At -0.9, 28/34 junk lines are flagged
        and 1/28 good ones.
        """
        if not text.strip():
            return TranslationResult("", True)
        tok = self._tok(src_lang)
        tokens = tok.convert_ids_to_tokens(tok.encode(text))
        result = self._translator.translate_batch(
            [tokens],
            target_prefix=[[nllb_code(tgt_lang)]],
            beam_size=self._beam_size,
            max_decoding_length=200,
            return_scores=True,
        )[0]
        out = result.hypotheses[0][1:]  # drop the target-language token
        decoded = tok.decode(tok.convert_tokens_to_ids(out), skip_special_tokens=True).strip()
        return TranslationResult(decoded, float(result.scores[0]) >= self._min_confidence)
