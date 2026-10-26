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
- 2026-10-26 · Speaker clustering threshold 0.4 (was an untuned 0.55). Measured with `scripts/eval_speakers.py` on 140
  clips / 7 known LibriSpeech speakers (English; no small Armenian set with speaker IDs exists), shuffled stream, 5 seeds:
  threshold 0.55 split 7 speakers into 21.6 clusters on 2 s clips; threshold 0.4 gave 7.4 / 7.0 / 7.0 clusters at 2 / 4 / 6 s,
  purity 100%. Different-speaker similarity p95 was 0.22 to 0.26, same-speaker mean 0.53 to 0.72. Caveats: clean read
  English, not compressed call audio or Armenian; similar voices may merge at 0.4. Status: Decided; recheck on a real call.
- 2026-10-26 · Bug found: SpeechBrain stored the speaker model as symlinks into the HF cache, so deleting the cache broke it.
  Now loaded with `LocalStrategy.COPY`; verified offline with an empty HF cache. Lesson: verify offline operation
  by running with an empty cache *before* deleting anything. Status: Fixed.
- 2026-10-26 · Server verified with real models: POST /api/sessions, WebSocket line stream and PostgreSQL-compatible storage
  (tested on SQLite) delivered 4 correct lines with latency. Web page connects and lists devices (checked in a browser).
  Bug fixed: WebSocket handler never noticed client disconnects, so dead clients blocked server shutdown. Status: Fixed.
- 2026-10-26 · Finding: a muted default output makes the system-audio monitor silent (no error is raised). Documented in
  README/TESTS rather than adding automatic handling. Status: Open (could warn when the monitor is silent at start).
- 2026-10-26 · Finding: when speakers feed the mic (echo, out of scope), every phrase is processed twice and latency rises
  to 4.5 to 6.8 s because one worker serializes ASR. Headphones avoid it. Status: Open.
- 2026-10-26 · Live feedback on the user's own voice (short phrases): ASR was mostly right, but the model prepends "- " and
  appends "…", which made NLLB translate "Ի՞նչպես ես…" as "How did you...". Fix: `clean_transcript` strips leading dashes and
  trailing ellipses before translating and displaying (keeps Armenian ՞ and ։). Status: Decided.
- 2026-10-26 · Translation beam size 4 (was 2). Scored on 40 FLEURS hy→en pairs with sacrebleu: beam 1 BLEU 35.7 / chrF 62.1
  (1.11 s), beam 2 38.2 / 64.4 (1.24 s), beam 4 39.7 / 65.0 (1.39 s), beam 5 39.9 / 64.5 (1.68 s). On one-word inputs beam 2
  gave "I'm going to tell you." for Բարև; beam 4 to 5 gave "How are you?". Status: Decided.
- 2026-10-26 · Known limit: NLLB-600M guesses on one-word inputs (Բարև → "Hi, how are you?", Ինչպես ես without ՞ → "Like I did").
  Options not taken yet: NLLB 1.3B distilled (about 2x slower, 5 GB download), a phrase glossary (hardcoded, rejected as a
  hidden fallback). The small ASR model heard "Լավ եմ" correctly where base dropped "եմ", but costs ~2.8 s on 1 s clips.
  Status: Open.
- 2026-10-26 · `--save-utterances DIR` saves each utterance's audio and transcript (data/ is git-ignored) for offline comparison.
