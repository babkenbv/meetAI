from __future__ import annotations

from pathlib import Path

from meetai.languages import nllb_code


class NllbTranslator:
    """NLLB-200 distilled 600M converted to CTranslate2 (int8), run on CPU."""

    def __init__(self, model_dir: str, tokenizer: str, cpu_threads: int = 4) -> None:
        import ctranslate2

        if not Path(model_dir).is_dir():
            raise FileNotFoundError(
                f"Translation model directory {model_dir!r} not found. Run scripts/convert_nllb.sh first."
            )
        self._translator = ctranslate2.Translator(
            model_dir, device="cpu", compute_type="int8", intra_threads=cpu_threads
        )
        self._tokenizer_name = tokenizer
        self._tokenizers: dict[str, object] = {}

    def _tok(self, src_lang: str):
        if src_lang not in self._tokenizers:
            from transformers import AutoTokenizer

            self._tokenizers[src_lang] = AutoTokenizer.from_pretrained(
                self._tokenizer_name, src_lang=nllb_code(src_lang)
            )
        return self._tokenizers[src_lang]

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        if not text.strip():
            return ""
        tok = self._tok(src_lang)
        tokens = tok.convert_ids_to_tokens(tok.encode(text))
        result = self._translator.translate_batch(
            [tokens], target_prefix=[[nllb_code(tgt_lang)]], beam_size=2, max_decoding_length=200
        )
        out = result[0].hypotheses[0][1:]  # drop the target-language token
        return tok.decode(tok.convert_tokens_to_ids(out), skip_special_tokens=True).strip()
