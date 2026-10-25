"""Measure ASR accuracy (WER/CER) and speed (real-time factor) on the evaluation slice.

Usage: python scripts/bench_asr.py --model models/asr [--eval data/eval] [--threads 4]
"""

import argparse

from meetai.asr.faster_whisper import FasterWhisperTranscriber
from meetai.evaluation import evaluate_asr, load_manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/asr")
    ap.add_argument("--eval", default="data/eval")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="only the first N samples")
    args = ap.parse_args()

    samples = load_manifest(args.eval)
    if args.limit:
        samples = samples[: args.limit]
    asr = FasterWhisperTranscriber(args.model, "int8", args.threads)
    asr.transcribe(samples[0].audio, "hy")  # warm-up, excluded from timing
    r = evaluate_asr(asr, samples)
    print(
        f"model={args.model} threads={args.threads} n={len(samples)}\n"
        f"WER={r.wer:.1%} CER={r.cer:.1%} RTF={r.rtf:.2f} slowest_utterance={r.max_seconds:.1f}s"
    )


if __name__ == "__main__":
    main()
