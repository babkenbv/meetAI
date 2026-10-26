"""Speaker identification. Mic audio is always `Me`; system audio is clustered online."""

from __future__ import annotations

from typing import Protocol

import numpy as np

from meetai.types import SAMPLE_RATE, Source, Utterance


class SpeakerEmbedder(Protocol):
    def embed(self, samples: np.ndarray) -> np.ndarray:
        """Returns a speaker embedding vector for 16 kHz mono float32 audio."""
        ...


class SpeechBrainEmbedder:
    """ECAPA-TDNN speaker embeddings (SpeechBrain), run locally on CPU."""

    def __init__(self, cache_dir: str = "models/spkrec-ecapa", threads: int = 1) -> None:
        import torch
        from speechbrain.inference.speaker import EncoderClassifier
        from speechbrain.utils.fetching import LocalStrategy

        # Runs in parallel with ASR: one thread keeps the two from fighting over the same cores.
        torch.set_num_threads(threads)
        self._torch = torch
        self._model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=cache_dir,
            run_opts={"device": "cpu"},
            local_strategy=LocalStrategy.COPY,  # real files, not symlinks into a deletable cache
        )

    def embed(self, samples: np.ndarray) -> np.ndarray:
        with self._torch.no_grad():
            emb = self._model.encode_batch(self._torch.from_numpy(samples).unsqueeze(0))
        return emb.squeeze().cpu().numpy()


class OnlineSpeakerClusterer:
    """Assigns a stable label to each embedding by cosine similarity to running centroids.

    A new speaker is created when no centroid is similar enough. Clips shorter than
    `min_embed_s` give unreliable embeddings, so they are not embedded: they inherit the
    label of the previous system-audio utterance (Speaker 1 if there is none).
    """

    def __init__(self, threshold: float = 0.4, min_embed_s: float = 1.0) -> None:
        self._threshold = threshold
        self.min_embed_s = min_embed_s
        self._centroids: list[np.ndarray] = []
        self._counts: list[int] = []
        self._last = 0

    @staticmethod
    def _unit(v: np.ndarray) -> np.ndarray:
        return v / (np.linalg.norm(v) + 1e-9)

    def assign_short(self) -> str:
        return f"Speaker {self._last + 1}"

    def assign(self, emb: np.ndarray) -> str:
        emb = self._unit(emb)
        if self._centroids:
            sims = [float(self._unit(c) @ emb) for c in self._centroids]
            best = int(np.argmax(sims))
            if sims[best] >= self._threshold:
                n = self._counts[best]
                self._centroids[best] = (self._centroids[best] * n + emb) / (n + 1)
                self._counts[best] = n + 1
                self._last = best
                return f"Speaker {best + 1}"
        self._centroids.append(emb)
        self._counts.append(1)
        self._last = len(self._centroids) - 1
        return f"Speaker {self._last + 1}"


class SpeakerLabeler:
    def __init__(self, embedder: SpeakerEmbedder, clusterer: OnlineSpeakerClusterer) -> None:
        self._embedder = embedder
        self._clusterer = clusterer

    def label(self, utt: Utterance) -> str:
        if utt.source is Source.MIC:
            return "Me"
        if len(utt.samples) / SAMPLE_RATE < self._clusterer.min_embed_s:
            return self._clusterer.assign_short()
        return self._clusterer.assign(self._embedder.embed(utt.samples))
