"""Record yourself reading known Armenian sentences, to measure ASR on your own voice and microphone.

Shows FLEURS reference sentences one at a time; read each aloud, press Enter to start recording and Enter again to
stop. Writes data/mine/NNN.wav and data/mine/manifest.tsv (usable with scripts/bench_asr.py --eval data/mine).
Usage: python scripts/record_eval.py [--count 8] [--mic SOURCE]
"""

import argparse
import select
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from meetai.audio.devices import default_source
from meetai.evaluation import load_manifest

OUT = Path("data/mine")


def record_until_enter(device: str) -> np.ndarray:
    proc = subprocess.Popen(
        ["parec", f"--device={device}", "--format=float32le", "--rate=16000", "--channels=1"], stdout=subprocess.PIPE
    )
    chunks = []
    try:
        while True:
            ready, _, _ = select.select([proc.stdout, sys.stdin], [], [], 0.2)
            if sys.stdin in ready:
                sys.stdin.readline()
                break
            if proc.stdout in ready:
                chunks.append(proc.stdout.read1(65536))
    finally:
        proc.terminate()
    data = b"".join(chunks)
    return np.frombuffer(data[: len(data) // 4 * 4], dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--mic")
    args = ap.parse_args()
    mic = args.mic or default_source("mic")

    # Shortest sentences first: easier to read in one go.
    samples = sorted(load_manifest("data/eval"), key=lambda s: len(s.reference))[: args.count]
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    for i, s in enumerate(samples):
        print(f"\n[{i + 1}/{len(samples)}] Read aloud:\n\n    {s.reference}\n")
        input("Press Enter, then read the sentence... ")
        print("Recording. Press Enter when done.")
        audio = record_until_enter(mic)
        name = f"{i:03d}.wav"
        sf.write(OUT / name, audio, 16000, subtype="PCM_16")
        lines.append(f"{name}\t{s.reference}")
        print(f"saved {len(audio) / 16000:.1f}s")
    (OUT / "manifest.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nDone: {len(lines)} recordings in {OUT}")


if __name__ == "__main__":
    main()
