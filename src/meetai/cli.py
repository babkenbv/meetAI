from __future__ import annotations

import argparse
import sys
import time

from meetai.audio.devices import default_source, list_sources
from meetai.config import Config
from meetai.format import format_line


def main(argv: list[str] | None = None) -> int:
    defaults = Config()
    p = argparse.ArgumentParser(prog="meetai", description="Live Armenian -> English transcription")
    p.add_argument("--list-devices", action="store_true", help="print audio sources and exit")
    p.add_argument("--mic", help="microphone source name (default: system default microphone)")
    p.add_argument("--system", help="system-audio monitor source name (default: monitor of default output)")
    p.add_argument("--asr-model", default=defaults.asr_model, help="fast ASR model, used for long utterances")
    p.add_argument("--asr-accurate-model", default=defaults.asr_accurate_model, help="slower, more accurate model for short phrases; '' disables")
    p.add_argument("--translation-model", default=defaults.translation_model)
    p.add_argument("--short-translation-model", default=defaults.translation_short_model, help="model for 1-2 word phrases; '' disables")
    p.add_argument("--save-utterances", metavar="DIR", help="debug: save each utterance (wav) and transcript to DIR")
    p.add_argument("--ignore-mic-check", action="store_true", help="keep going when the startup mic check fails (prints the problem)")
    p.add_argument("--show-latency", action="store_true", help="append end-of-phrase -> output latency")
    args = p.parse_args(argv)

    if args.list_devices:
        for d in list_sources():
            kind = "system (monitor)" if d.is_monitor else "microphone"
            print(f"{d.index:>3}  {kind:<17} {d.name}")
        return 0

    from meetai.session import Session  # heavy imports only when actually running

    cfg = Config(
        asr_model=args.asr_model,
        asr_accurate_model=args.asr_accurate_model or None,
        translation_model=args.translation_model,
        translation_short_model=args.short_translation_model or None,
    )
    mic = args.mic or default_source("mic")
    system = args.system or default_source("system")
    print(f"mic: {mic}\nsystem: {system}\nLoading models...", file=sys.stderr)

    session = Session(
        cfg, mic, system, [lambda line: print(format_line(line, args.show_latency), flush=True)], args.save_utterances,
        strict_mic_check=not args.ignore_mic_check,
    )
    session.start()
    print("Listening. Ctrl+C to stop.", file=sys.stderr)
    try:
        while True:
            session.check()
            time.sleep(0.2)
    except KeyboardInterrupt:
        return 0
    finally:
        session.stop()


if __name__ == "__main__":
    raise SystemExit(main())
