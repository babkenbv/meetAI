# meetAI

Live Armenian → English transcription for calls. Captures the microphone (`Me`) and the system audio
(`Speaker 1`, `Speaker 2`, …), transcribes and translates locally, and prints
`[HH:MM:SS] Speaker  HY: …  EN: …` per phrase. All models run on your machine; nothing is sent to a cloud API.

Stack: Python, faster-whisper (ASR), CTranslate2 + NLLB-200 (translation), Silero VAD, SpeechBrain ECAPA
speaker embeddings with online clustering, FastAPI + WebSockets, Next.js/React/TypeScript/Tailwind,
PostgreSQL, Docker. CPU is the baseline; a GPU is an optimization, not a requirement.

## Setup (Linux, PulseAudio or PipeWire)

```bash
python3 -m virtualenv .venv && . .venv/bin/activate
pip install -e ".[server,dev]"
scripts/convert_nllb.sh                   # NLLB-200 600M -> models/nllb-600m-ct2
scripts/convert_opus.sh                    # OPUS-MT hy-en -> models/opus-hy-en-ct2
scripts/convert_asr.sh Chillarmo/whisper-base-armenian models/asr-base   # ASR model
```

System audio is the `.monitor` source of your output device, so no loopback driver is needed on Linux
(macOS needs BlackHole or similar). List sources with `meetai --list-devices`.

### Troubleshooting: no system-audio lines

The system source is the *monitor* of your output device, so it only carries sound while the output is **not
muted** and something is playing. A muted output gives pure silence (`pactl list sinks | grep Mute`;
`pactl set-sink-mute @DEFAULT_SINK@ 0` to unmute). Use `python scripts/live_check.py` to play a test clip
through the pipeline.

## Run

```bash
meetai --show-latency                      # terminal
meetai --mic <source> --system <monitor>   # explicit devices
```

Web app: start Postgres (`docker compose up db`), then

```bash
DATABASE_URL=postgresql+psycopg://meetai:meetai@localhost:5432/meetai uvicorn meetai.server.main:app
cd web && npm install && npm run dev       # http://localhost:3000
```

or everything with `docker compose up --build` (models are mounted from `./models`).

## Architecture

`audio/` (parec capture per source) → `vad.py` (Silero, one segmenter per source) → `speakers.py`
(`Me` for mic; ECAPA embeddings + online cosine clustering for system audio) → `asr/` → `translate/` →
sinks (terminal, WebSocket, PostgreSQL). ASR, translation and speaker embedding sit behind small interfaces
(`Transcriber`, `Translator`, `SpeakerEmbedder`) so the deployment (local, private, managed) can change
without touching the pipeline. The data model stores source and target language per row.

## Models and measurements (this machine: i7-8565U, 4 cores, no GPU)

| Part | Choice | Why |
|---|---|---|
| ASR | `Chillarmo/whisper-base-armenian`, faster-whisper int8 | WER 33% / CER 9% on 40 FLEURS hy_am clips, RTF 0.14. The small model is 27% / 8.9% but 2.5x slower and breaks the 5 s budget. BuzzASR (large-v3 size, 3.1 GB) was rejected as too heavy for CPU. |
| Translation | NLLB-200 distilled 600M (sentences) + OPUS-MT hy-en (1-2 word phrases), CTranslate2 int8 | NLLB BLEU 39.7 on 40 FLEURS sentences but guesses on one-word greetings; OPUS gets greetings right but BLEU 20.7 on sentences. MADLAD-400 3B was measured too: no better on sentences, 5.8 GB RAM. NLLB is CC-BY-NC. |
| VAD | Silero VAD (ONNX) | Small, accurate, runs per 32 ms chunk. |
| Speakers | SpeechBrain ECAPA embeddings + online cosine clustering | Works on a live stream; offline diarization (pyannote) needs the whole recording. |

Reproduce: `python scripts/fetch_eval.py`, then `scripts/bench_asr.py`, `scripts/bench_translate.py`, `scripts/bench_e2e.py`;
speakers: `python scripts/fetch_speakers.py` then `python scripts/eval_speakers.py`.
Setup details are in `DECISIONS.md`. Downloads are large (about 3.5 GB originals; 0.9 GB after conversion) and
`models/hf` can be deleted once `models/asr-base` and `models/nllb-600m-ct2` exist.

## Known limitations

- Armenian accuracy is limited (WER ~33%): names, numbers and fast speech are often wrong, and translation inherits the errors.
- Latency is ~3 s for one speaker, but can exceed 5 s when mic and system audio are busy at the same time
  (one CPU worker serializes ASR). Mic pickup of the speakers (echo) makes this worse and is out of scope.
- Long utterances are cut at 6 s to bound latency, which can split a sentence and hurt translation.
- Speaker labels: the threshold (0.4) was tuned on clean English speech (7 speakers: right count, 100% purity), not on
  Armenian call audio. Clips under 1 s inherit the previous label, and similar voices can merge.
- Eastern Armenian (FLEURS hy_am) was used for evaluation; Western Armenian is untested.
- Not yet measured: live accuracy with two real voices on a call.

## Verification status

| Area | Status |
|---|---|
| Unit tests (23) | Pass |
| CLI live run, system audio, real models | Works (played FLEURS clips; lines in 2.6 to 4.5 s) |
| Speaker clustering | Tuned on 7 English speakers; not yet checked on a real Armenian call |
| API + WebSocket + DB with real models | Works (SQLite); PostgreSQL via Docker not run |
| Web page | Connects, lists devices; live transcript view not watched end to end in the browser |
| Docker images | `docker compose config` valid; images not built |
| Latency with echo (speakers into mic) | Can exceed 5 s |
