from __future__ import annotations

from meetai.types import Line


def format_clock(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def format_line(line: Line, show_latency: bool = False) -> str:
    text = (
        f"[{format_clock(line.t_start)}] {line.speaker:<10} "
        f"{line.src_lang.upper()}: {line.src_text}  {line.tgt_lang.upper()}: {'' if line.tgt_confident else '[unsure] '}{line.tgt_text}"
    )
    if show_latency:
        text += f"  ({line.latency_s:.1f}s)"
    return text
