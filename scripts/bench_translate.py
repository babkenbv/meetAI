"""Time hy->en translation on the evaluation references and print samples for eyeballing.

Usage: python scripts/bench_translate.py [--eval data/eval] [--limit 10]
"""

import argparse
import time

from meetai.config import Config
from meetai.evaluation import load_manifest
from meetai.translate.nllb_ct2 import NllbTranslator


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default="data/eval")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()

    cfg = Config()
    mt = NllbTranslator(cfg.translation_model, cfg.translation_tokenizer, args.threads)
    samples = load_manifest(args.eval)[: args.limit]
    mt.translate(samples[0].reference, "hy", "en")  # warm-up
    total = 0.0
    for s in samples:
        t0 = time.perf_counter()
        en = mt.translate(s.reference, "hy", "en")
        dt = time.perf_counter() - t0
        total += dt
        print(f"[{dt:.2f}s] HY: {s.reference}\n        EN: {en}\n")
    print(f"mean={total / len(samples):.2f}s per sentence over {len(samples)}")


if __name__ == "__main__":
    main()
