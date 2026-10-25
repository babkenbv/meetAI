"""Tune speaker clustering on data/speakers (see fetch_speakers.py).

For each clip length, reports same-vs-different speaker cosine similarity and, for a sweep of thresholds,
how the online clusterer behaves on a shuffled stream: clusters found (true: 7) and purity (share of utterances
whose cluster's majority speaker is their own speaker).
"""

import argparse
import collections
from pathlib import Path

import numpy as np
import soundfile as sf

from meetai.speakers import OnlineSpeakerClusterer, SpeechBrainEmbedder

SR = 16000


def purity(assigned: list[str], truth: list[str]) -> float:
    by_cluster = collections.defaultdict(list)
    for a, t in zip(assigned, truth):
        by_cluster[a].append(t)
    correct = sum(collections.Counter(v).most_common(1)[0][1] for v in by_cluster.values())
    return correct / len(truth)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/speakers")
    ap.add_argument("--lengths", type=float, nargs="+", default=[2.0, 4.0, 6.0])
    ap.add_argument("--seeds", type=int, default=5)
    args = ap.parse_args()

    rows = [l.split("\t") for l in Path(args.dir, "manifest.tsv").read_text().splitlines()]
    clips = [(sf.read(Path(args.dir, f), dtype="float32")[0], spk.strip()) for f, spk in rows]
    truth = [s for _, s in clips]
    embedder = SpeechBrainEmbedder()

    for length in args.lengths:
        embs = np.stack([embedder.embed(a[: int(length * SR)]) for a, _ in clips])
        embs /= np.linalg.norm(embs, axis=1, keepdims=True)
        sims = embs @ embs.T
        same = np.array([[truth[i] == truth[j] and i != j for j in range(len(truth))] for i in range(len(truth))])
        diff = np.array([[truth[i] != truth[j] for j in range(len(truth))] for i in range(len(truth))])
        print(
            f"\n== first {length:.0f}s of each clip ==\n"
            f"same-speaker sim: mean {sims[same].mean():.2f} p5 {np.percentile(sims[same], 5):.2f} | "
            f"different-speaker sim: mean {sims[diff].mean():.2f} p95 {np.percentile(sims[diff], 95):.2f}"
        )
        print("threshold  clusters(true 7)  purity")
        for th in (0.3, 0.4, 0.5, 0.55, 0.6, 0.7, 0.8):
            ks, ps = [], []
            for seed in range(args.seeds):
                order = np.random.default_rng(seed).permutation(len(clips))
                c = OnlineSpeakerClusterer(th)
                assigned = [c.assign(embs[i]) for i in order]
                ks.append(len(set(assigned)))
                ps.append(purity(assigned, [truth[i] for i in order]))
            print(f"{th:>8.2f}  {np.mean(ks):>10.1f}  {np.mean(ps):>12.1%}")


if __name__ == "__main__":
    main()
