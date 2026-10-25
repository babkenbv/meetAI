# Decision log

Format: date · decision · why · status (Decided / Open / Unverified).

- 2026-10-24 · Build a terminal-only Python program; web stack (Next.js/Postgres/Redis/WebSockets) deferred.
  Why: the brief says a terminal is enough and the time budget is ~20 h. Status: Decided.
- 2026-10-24 · Baseline hardware is this CPU-only machine (8 cores, 11 GB RAM, no GPU). Status: Decided.
- 2026-10-24 · Use Claude Code for the project (brief says Claude Cowork). User accepted; chat export handled separately. Status: Decided.
- 2026-10-24 · Process: plan and model research first, then walking skeleton. Status: Decided.
- 2026-10-24 · ASR model: Open. `BuzzASR/armenian` reports WER 7.5% but is self-reported and large-v3-sized.
  Needs benchmark for accuracy and CPU RTF. Status: Unverified.
- 2026-10-24 · MT model: Open. NLLB-200 distilled 600M (CT2 int8) is the lead; Armenian code `hye_Armn` and
  hy→en quality not yet verified. Status: Unverified.
- 2026-10-24 · Diarization approach: Open. Online embedding + incremental clustering preferred over offline pyannote. Status: Open.
- 2026-10-24 · ASR model: `Chillarmo/whisper-small-armenian-v2` (Whisper small, ~244M params, Apache-2.0) instead of
  `BuzzASR/armenian` (large-v3, 3.1 GB download, likely too slow on 8-core CPU, no smaller BuzzASR variant exists).
  Self-reported Common Voice 20 held-out WER 24.0% / CER 4.8%; read speech, so real conversation will be worse.
  Fallback if accuracy is too low and speed allows: `Chillarmo/whisper-large-v3-turbo-hy-ct2` (pre-converted, 1.6 GB).
  Status: chosen for the walking skeleton; to be confirmed by benchmark on this machine.
- 2026-10-25 · ASR model (revised): `Chillarmo/whisper-base-armenian` (CT2 int8, `models/asr-base`) is the default.
  Measured on this i7-8565U (4 cores, AVX2, 4 threads), 40 FLEURS hy_am dev clips:
  | model | WER | CER | RTF |
  |---|---|---|---|
  | whisper-small-armenian-v2 | 27.3% | 8.9% | 0.36 to 0.59 |
  | whisper-base-armenian | 33.2% | 9.0% | 0.14 |
  Why base: Whisper pads to 30 s, so small has a ~2.7 s floor per utterance and cannot reliably fit the 5 s budget
  once VAD wait (0.5 s), translation (~1 s) and speaker embedding are added; CER is almost identical. Small stays
  available via `--asr-model models/asr`. 8 threads was slower than 4 (hyperthreads contend). Status: Decided.
- 2026-10-25 · Translation: NLLB-200 distilled 600M, CT2 int8 (`models/nllb-600m-ct2`, tokenizer saved beside it).
  ~1.0 s per sentence on 4 threads; output on 6 FLEURS references was fluent and correct. License CC-BY-NC (fine for
  the challenge, blocks commercial use). Status: Decided.
- 2026-10-25 · Latency: max utterance 6 s (was 8 s), speaker embedding runs in parallel with ASR, all models warmed up at
  start (first MT call took 8.7 s cold). Replay benchmark (`scripts/bench_e2e.py`, 22 utterances): mean 1.8 s, max 2.6 s
  processing + 0.5 s VAD wait. Status: Decided.
- 2026-10-25 · Speaker clustering threshold 0.55 is untuned: no multi-speaker ground truth yet. FLEURS has no speaker IDs
  here. Needs real two-person recordings. Status: Open.
