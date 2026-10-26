from __future__ import annotations

import re

_LEADING = re.compile(r"^[\s\-‐-―]+")  # dialogue dashes the ASR model likes to prepend
_TRAILING = re.compile(r"[\s…]+$|\.{2,}$")  # trailing ellipsis (… or ...)
_ELLIPSIS_MID = re.compile(r"…")
_SPACES = re.compile(r"\s+")
_BROKEN_TAIL = re.compile(r"\ufffd+$")  # half a UTF-8 character left when decoding stops mid-token


def clean_transcript(text: str) -> str:
    """Remove ASR artifacts that mislead translation: leading dashes, ellipses, doubled spaces.

    Armenian punctuation (the question mark ՞ on the stressed word, ։ full stop) is kept: it carries meaning.
    """
    text = _BROKEN_TAIL.sub("", text.rstrip())
    text = _ELLIPSIS_MID.sub(" ", text)
    text = _LEADING.sub("", text)
    text = _TRAILING.sub("", text)
    return _SPACES.sub(" ", text).strip()
