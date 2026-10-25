"""Replay evaluation clips as a system-audio stream and measure per-utterance processing time.

Expected end-of-phrase -> English latency = min_silence_s (VAD waits for it) + processing time reported here.
Usage: python scripts/bench_e2e.py [--limit 12] [--max-utterance 5]
"""

import argparse
import time

import numpy as np

from meetai.asr.faster_whisper import FasterWhisperTranscriber
from meetai.audio.capture import CHUNK_SAMPLES
from meetai.config import Config
from meetai.evaluation import load_manifest
from meetai.pipeline import Pipeline
from meetai.speakers import OnlineSpeakerClusterer, SpeakerLabeler, SpeechBrainEmbedder
from meetai.translate.nllb_ct2 import NllbTranslator
from meetai.types import SAMPLE_RATE, AudioChunk, Source
from meetai.vad import Segmenter, load_silero


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default="data/eval")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--max-utterance", type=float, default=Config.max_utterance_s)
    ap.add_argument("--threads", type=int, default=Config.cpu_threads)
    ap.add_argument("--asr", default=Config.asr_model)
    args = ap.parse_args()
    cfg = Config(max_utterance_s=args.max_utterance, cpu_threads=args.threads, asr_model=args.asr)

    asr = FasterWhisperTranscriber(cfg.asr_model, cfg.asr_compute_type, cfg.cpu_threads)
    mt = NllbTranslator(cfg.translation_model, cfg.translation_tokenizer, cfg.cpu_threads)
    labeler = SpeakerLabeler(SpeechBrainEmbedder(), OnlineSpeakerClusterer(cfg.speaker_threshold, cfg.min_embed_s))
    seg = Segmenter(Source.SYSTEM, load_silero(), cfg.vad_threshold, cfg.min_silence_s, cfg.min_speech_s, cfg.max_utterance_s)
    lines = []
    pipe = Pipeline({Source.SYSTEM: seg}, labeler, asr, mt, "hy", "en", [lines.append])
    pipe.warm_up()

    gap = np.zeros(SAMPLE_RATE * 1, np.float32)
    stream = np.concatenate([np.concatenate([s.audio, gap]) for s in load_manifest(args.eval)[: args.limit]])
    stream = stream[: len(stream) // CHUNK_SAMPLES * CHUNK_SAMPLES]

    totals = []
    for i in range(0, len(stream), CHUNK_SAMPLES):
        utt = seg.feed(AudioChunk(Source.SYSTEM, stream[i : i + CHUNK_SAMPLES], i / SAMPLE_RATE))
        if utt is None:
            continue
        t0 = time.perf_counter()
        pipe._process(utt)  # same code path as live, minus queueing
        total = time.perf_counter() - t0
        totals.append(total)
        line = lines[-1] if lines else None
        print(f"{len(utt.samples) / SAMPLE_RATE:4.1f}s audio | {total:.2f}s | {line.speaker if line else '-'} | {line.tgt_text[:70] if line else ''}")
    print(
        f"utterances={len(totals)} mean={np.mean(totals):.2f}s max={max(totals):.2f}s "
        f"-> worst-case latency ~ {cfg.min_silence_s + max(totals):.1f}s (budget 5s)"
    )


if __name__ == "__main__":
    main()
