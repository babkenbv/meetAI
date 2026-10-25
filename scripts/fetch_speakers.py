"""Download a tiny public multi-speaker set to tune speaker clustering.

Uses sanchit-gandhi/librispeech_asr_dummy: each of its splits holds 20 clips of one LibriSpeech speaker, so
combining all splits gives several speakers with known IDs. Speaker identity does not depend on language, and no
small Armenian set with speaker IDs exists. Writes data/speakers/<n>.wav and manifest.tsv (`file<TAB>speaker_id`).
"""

import io
from pathlib import Path

import pyarrow.parquet as pq
import soundfile as sf
from huggingface_hub import HfApi, hf_hub_download

OUT = Path("data/speakers")


REPO = "sanchit-gandhi/librispeech_asr_dummy"


def main() -> None:
    files = [f for f in HfApi().list_repo_files(REPO, repo_type="dataset") if f.startswith("data/") and f.endswith(".parquet")]
    OUT.mkdir(parents=True, exist_ok=True)
    lines, n = [], 0
    for f in sorted(files):
        for row in pq.read_table(hf_hub_download(REPO, f, repo_type="dataset")).to_pylist():
            audio, rate = sf.read(io.BytesIO(row["audio"]["bytes"]), dtype="float32")
            if rate != 16000 or audio.ndim != 1:
                raise ValueError(f"{f}: expected 16 kHz mono, got {rate} Hz {audio.shape}")
            name = f"{n:03d}.wav"
            sf.write(OUT / name, audio, rate, subtype="PCM_16")
            lines.append(f"{name}\t{row['speaker_id']}")
            n += 1
    (OUT / "manifest.tsv").write_text("\n".join(lines) + "\n")
    print(f"Wrote {n} clips, {len({l.split(chr(9))[1] for l in lines})} speakers to {OUT}")


if __name__ == "__main__":
    main()
