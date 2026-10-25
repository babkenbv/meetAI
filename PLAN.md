# PLAN: Live Armenian → English transcription (meetAI)

## Goal
A Python terminal program that captures **microphone** (`Me`) and **system audio** (`Speaker N`) at the same
time, transcribes Armenian locally, translates to English locally, and prints
`[HH:MM:SS] Speaker  HY: …  EN: …` within **5 s** of the end of a phrase.
Source of truth: the Mathrix challenge brief. Local models only, no cloud APIs, no weights/audio/keys in git.

## Target hardware (measured 2026-10-24)
x86_64 Linux, 8 CPU cores, **no usable GPU**, 11 GB RAM (~4.6 GB free), ~6.6 GB free disk, Python 3.10,
PulseAudio/PipeWire (system audio = the `*.monitor` source). CPU-only is the baseline.
**Consequence:** a 1.5B-param ASR model (Whisper large-v3 size) is probably too slow for the 5 s budget.
Every model choice must be backed by a measured real-time factor (RTF) on this machine.

## Out of scope (per brief)
GUI, installer, echo handling, named/persistent speakers, saving transcripts, non-Armenian input.
The pasted product stack (Next.js, Postgres, Redis, WebSockets) is for a future product, not this challenge.
We keep only the **model interfaces** swappable and `language` as a parameter, not hardcoded.

## Modules (one responsibility, plain data in/out)
| Module | Input | Output |
|---|---|---|
| `audio/` capture | device name | stream of `AudioChunk(source: "mic"|"system", samples: float32 16 kHz mono, t_start)` |
| `vad/` segmenter | `AudioChunk` stream | `Utterance(source, samples, t_start, t_end)` (speech ended → emit) |
| `speakers/` | `Utterance` | `speaker_label` (`Me` for mic; online embedding + clustering for system) |
| `asr/` | `Utterance` | `hy_text` |
| `translate/` | `hy_text` | `en_text` |
| `pipeline` + `cli` | all of the above | formatted terminal lines, device list/selection flags |

Model access sits behind small interfaces (`Transcriber`, `Translator`, `SpeakerEmbedder`) so a model can be
swapped without touching the pipeline. No fallbacks: a missing model or device fails loudly.

## Candidate models (HYPOTHESES to verify, not decisions)
- **ASR:** Whisper-family via faster-whisper (CTranslate2, int8 on CPU). Candidates: `BuzzASR/armenian`
  (large-v3 fine-tune, self-reported WER 7.5%, likely too heavy), smaller community fine-tunes
  (tiny/small, reported WER 40–78%, likely too inaccurate), zero-shot Whisper small/medium/large-v3-turbo,
  MMS-1b (`hy` adapter). Need CT2 conversion + disk budget check (6.6 GB free).
- **Translation hy→en:** NLLB-200 distilled 600M via CTranslate2 int8 (license CC-BY-NC, fine for the
  challenge; note in README). Alternatives: OPUS-MT if an hy-en model exists, a small LLM.
- **VAD:** Silero VAD. **Diarization:** online speaker embeddings (e.g. WeSpeaker/ECAPA/CAM++ via ONNX)
  + incremental clustering, because the brief needs stable labels in a live stream, not offline pyannote.
- Anything above that I could not confirm from primary sources is flagged in `DECISIONS.md`.

## Milestones
1. **Eval set + benchmark harness**: small public Armenian slice (FLEURS/Common Voice, with permission to
   download) + your own recordings. Measure WER/CER, RTF and latency per candidate ASR/MT model.
2. **Pick models** from numbers → write `DECISIONS.md` entries.
3. **Walking skeleton**: mic only → VAD → ASR → MT → terminal, end to end.
4. **Add system audio** as a second source (PulseAudio monitor), same pipeline.
5. **Speaker identification** on the system stream; test label stability.
6. **Latency pass**: improve the weakest link measured against the 5 s budget.
7. **README, TESTS.md, chat exports** in `chats/`.

## Testing (derived from the brief, not from the code)
See `TESTS.md`. Core checks: two sources captured simultaneously; mic always `Me`; ≥2 distinct system
speakers get distinct, persistent labels; end-of-phrase → EN line ≤ 5 s; output has time/speaker/HY/EN;
no network calls at runtime (offline run); no weights/audio/keys committed.

## Risks
1. CPU-only latency vs. Armenian ASR accuracy (main risk). Mitigation: benchmark early, smaller model, shorter segments.
2. Disk (6.6 GB free) and RAM (4.6 GB free) limit model sizes. Mitigation: int8, one model at a time during benchmarks.
3. Online diarization on short utterances is unreliable. Mitigation: minimum segment length, honest limits in README.
4. Translation of ASR errors compounds. Mitigation: measure end-to-end, not per-module only.
5. Western vs Eastern Armenian mismatch in models/data. Mitigation: confirm which variant the interview uses.
