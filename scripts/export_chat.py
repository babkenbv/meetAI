"""Convert a Claude Code session export (transcript.jsonl) to one Markdown file.

Keeps every user message, assistant message, reasoning block, tool call and tool result in order, unedited. Not
included: metadata records (API request blobs, file-history snapshots, system/context attachments). Embedded images
(base64) are replaced by a one-line placeholder with their size.

Redactions (listed in the output header): the result of a session-listing call that names the author's unrelated
projects, and the two project names quoted in the assistant's reply to it.

Usage: python scripts/export_chat.py transcript.jsonl chats/<name>.md
"""

import json
import sys
from pathlib import Path


def text_of(content) -> str:
    """Plain text of a message content (string, or a list of blocks)."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if block.get("type") == "text":
            parts.append(block["text"])
        elif block.get("type") == "image":
            size = len(block.get("source", {}).get("data", ""))
            parts.append(f"[image omitted: {block.get('source', {}).get('media_type', 'image')}, {size} base64 chars]")
        else:
            parts.append(json.dumps(block, ensure_ascii=False))
    return "\n".join(parts)


REDACTED_LISTING = "[redacted: output of a session-listing call that named the author's unrelated projects]"
# Exact phrases from the assistant's reply to that listing.
TEXT_REDACTIONS = {"(they are different projects such as fumo and aroma-book)": "(they are different, unrelated projects)"}


def redact_tool_result(body: str) -> tuple[str, bool]:
    if body.lstrip().startswith("[") and '"sessionId": "local_' in body and '"title":' in body:
        return REDACTED_LISTING, True
    return body, False


def redact_text(text: str) -> tuple[str, int]:
    n = 0
    for old, new in TEXT_REDACTIONS.items():
        if old in text:
            text, n = text.replace(old, new), n + 1
    return text, n


def fence(text: str, lang: str = "") -> str:
    ticks = "```"
    while ticks in text:
        ticks += "`"
    return f"{ticks}{lang}\n{text}\n{ticks}"


def convert(src: Path) -> str:
    redactions = {"tool results": 0, "text phrases": 0}
    records = [json.loads(line) for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
    conv = [r for r in records if r.get("type") in ("user", "assistant") and isinstance(r.get("message"), dict)]
    session = next((r["sessionId"] for r in conv), "unknown")
    first, last = conv[0]["timestamp"], conv[-1]["timestamp"]
    model = next((r["message"].get("model") for r in conv if r["type"] == "assistant"), "unknown")
    out = [
        f"# Chat transcript: meetAI (Claude Code session {session})",
        "",
        f"- Tool: Claude Code (desktop app), model `{model}`",
        f"- Period: {first} to {last}",
        f"- Messages: {len(conv)} (user and assistant records, including tool calls and tool results)",
        "- Exported with the app's session export, converted by `scripts/export_chat.py`. Content is unedited; embedded images are",
        "  replaced by a placeholder. Metadata records (API request blobs, file-history snapshots, system attachments) are not included.",
        "",
        "---",
        "",
    ]
    for r in conv:
        msg, ts = r["message"], r["timestamp"]
        content = msg["content"]
        if r["type"] == "user":
            if isinstance(content, str):
                out += [f"## User ({ts})", "", content, ""]
                continue
            for block in content:
                kind = block.get("type")
                if kind == "tool_result":
                    body = text_of(block["content"]) if "content" in block else ""
                    body, hit = redact_tool_result(body)
                    redactions["tool results"] += hit
                    err = " (error)" if block.get("is_error") else ""
                    out += [f"### Tool result{err} ({ts})", "", fence(body), ""]
                else:
                    out += [f"## User ({ts})", "", text_of([block]), ""]
        else:
            for block in content:
                kind = block.get("type")
                if kind == "text":
                    body, n = redact_text(block["text"])
                    redactions["text phrases"] += n
                    out += [f"## Assistant ({ts})", "", body, ""]
                elif kind == "thinking":
                    out += [f"### Assistant reasoning ({ts})", "", fence(block.get("thinking", "")), ""]
                elif kind == "tool_use":
                    out += [f"### Tool call: {block['name']} ({ts})", "", fence(json.dumps(block["input"], ensure_ascii=False, indent=2), "json"), ""]
                else:
                    out += [f"### {kind} ({ts})", "", fence(json.dumps(block, ensure_ascii=False)), ""]
    note = (
        f"- Redactions: {redactions['tool results']} tool result and {redactions['text phrases']} text phrase(s) replaced "
        "(names of the author's unrelated projects); nothing else was changed."
    )
    out.insert(7, note)
    return "\n".join(out)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(convert(src), encoding="utf-8")
    print(f"wrote {dst} ({dst.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
