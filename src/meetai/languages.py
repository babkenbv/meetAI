"""Language registry. The data model is multilingual; only hy -> en is implemented."""

from __future__ import annotations

# ISO 639-1 code -> (Whisper language code, NLLB-200 code, display name)
LANGUAGES: dict[str, tuple[str, str, str]] = {
    "hy": ("hy", "hye_Armn", "Armenian"),
    "en": ("en", "eng_Latn", "English"),
}


def nllb_code(lang: str) -> str:
    return LANGUAGES[lang][1]


def whisper_code(lang: str) -> str:
    return LANGUAGES[lang][0]
