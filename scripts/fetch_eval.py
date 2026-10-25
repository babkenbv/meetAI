"""Download a small Armenian (Eastern, hy_am) evaluation slice from Google FLEURS (dev split).

Writes data/eval/<id>.wav (16 kHz mono 16-bit) and data/eval/manifest.tsv. Run once; data/ is git-ignored.
Usage: python scripts/fetch_eval.py [--count 40]
"""

import argparse
import csv
import io
import tarfile
from pathlib import Path

import soundfile as sf
from huggingface_hub import hf_hub_download

OUT = Path("data/eval")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=40)
    args = ap.parse_args()

    tsv = hf_hub_download("google/fleurs", "data/hy_am/dev.tsv", repo_type="dataset")
    archive = hf_hub_download("google/fleurs", "data/hy_am/audio/dev.tar.gz", repo_type="dataset")

    # FLEURS tsv columns: id, file_name, raw_transcription, transcription, phonemes, num_samples, gender
    refs: dict[str, str] = {}
    with open(tsv, encoding="utf-8", newline="") as f:
        for row in csv.reader(f, delimiter="\t"):
            refs[row[1]] = row[2]

    OUT.mkdir(parents=True, exist_ok=True)
    lines = []
    with tarfile.open(archive) as tar:
        for member in tar:
            name = Path(member.name).name
            if not member.isfile() or name not in refs:
                continue
            audio, rate = sf.read(io.BytesIO(tar.extractfile(member).read()), dtype="float32")
            if rate != 16000 or audio.ndim != 1:
                raise ValueError(f"{name}: expected 16 kHz mono, got {rate} Hz, shape {audio.shape}")
            sf.write(OUT / name, audio, rate, subtype="PCM_16")
            lines.append(f"{name}\t{refs[name]}")
            if len(lines) >= args.count:
                break
    (OUT / "manifest.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} samples to {OUT}")


if __name__ == "__main__":
    main()
