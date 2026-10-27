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
- 2026-10-26 · Two ASR models: base (fast) for long utterances, small (accurate) for utterances <= 2 s when nothing is queued.
  On the user's 6 short recordings small heard "Բարև" every time and "Լավ եմ" correctly; base misheard "Բարավ" and dropped
  "եմ". Beam 5 did not help base (worse). Small costs ~2.7 s even for 1 s clips (30 s input padding), so it self-limits: if
  an accurate-path utterance exceeds 3.8 s (5 s - 0.5 s VAD - margin), the fast model is used for 30 s, then it retries.
  Reason: Chrome (call app) and CPU heat made timings vary by up to 2x during testing. Status: Decided.
- 2026-10-26 · Tried and reverted: capping ASR output at 22 tokens/s + 6 (to stop hallucination loops). It raised FLEURS WER
  from 33.2% to 45.9% and did not reduce latency (likely interacts with Whisper's temperature fallback). Lesson: measure
  before keeping. Hallucinated long text on sub-second clips remains an open issue. Status: Rejected.
- 2026-10-26 · NLLB n-best check: for Բարև the 600M model's top 6 candidates are all conversational ("How are you?",
  "What's up?"), none is "Hi". Not fixable by decoding options. Status: Known limitation.
- 2026-10-26 · Short-clip hallucination: on ~1 s clips the small model sometimes decoded ~10 invented words (88 chars), costing
  up to 5.0 s. Not caused by temperature fallback (identical with fallback off). Volume normalization and 0.5 s padding did not help
  (normalization made it worse: one clip 24 s). Fix: cap output at 22 tokens/s + 6 for clips under 4 s only. Result on the user's
  11 clips: small max 5.0 s to 3.0 s, longest text 88 to 25 chars; FLEURS WER unchanged (29.8% base / 30.1% small on 20 clips).
  Note: on FLEURS the small model is no clearly better than base (30.1% vs 29.8% on 20 clips; 27.3% vs 33.2% on 40); its edge
  is on the user's short greetings ("Բարև" 5/5 vs 3/5). Status: Decided, but the evidence for small is thin (11 clips, one speaker).
- 2026-10-26 · ASR on the user's own voice (7 FLEURS sentences read aloud, `scripts/record_eval.py`; clip 0 was a greeting, excluded):
  base WER 52.6% / CER 16.2% (1.2 to 1.5 s); small WER 45.1% / CER 10.7% (3.3 to 4.7 s). FLEURS studio speakers give 30% /
  9% for the same models, so voice, mic and conversational speech cost roughly 20 points of WER. Most errors are near-miss
  spellings (սեզոնի → սազոնեի). Beam 3/5, no-timestamps decoding gave no gain on base. Small is clearly better on this voice but
  3 to 5 s for 5-6 s sentences, which breaks the 5 s budget with translation and the VAD wait. Status: Known limitation.
- 2026-10-26 · Tried `yervandgaloyan/whisper-base-hy` as an alternative base model: incompatible (loads as English-only tokenizer, crashes
  in faster-whisper). Dropped. Not tried: other small/base fine-tunes, a headset mic. Status: Rejected.
- 2026-10-26 · A broken trailing character ("կի�") came from the short-clip token cap cutting a UTF-8 character; `clean_transcript`
  now strips it. Status: Fixed.
- 2026-10-26 · Translation model comparison (user disliked NLLB-600M). FLEURS hy→en, sacrebleu, 4 threads, CT2 int8:
  | model | 40 sentences BLEU / chrF | same 8 sentences BLEU / chrF | s/sentence | RAM | 10 short phrases (my judgment) |
  |---|---|---|---|---|---|
  | NLLB-200 distilled 600M, beam 4 | 39.7 / 65.0 | 44.8 / 68.6 | 1.8 | ~0.7 GB | ~5 right (Բարև → "What's going on?") |
  | MADLAD-400 3B-MT (community int8: Nextcloud-AI/madlad400-3b-mt-ct2-int8) | not run | 38.8 / 63.5 | 5.1 (max 9.8) | 5.8 GB RSS | 10 right (Բարև → "Hello.") |
  | OPUS-MT hy-en (Helsinki-NLP, 2019) | 20.7 / 45.7 | not run | 0.3 | ~0.1 GB | 8 right (Բարև → "Hi", Ցտեսություն → "TEPA") |
  MADLAD is best on short phrases but worse than NLLB on sentences, 3x slower, and 5.8 GB RSS on an 11 GB machine that is
  already swapping (rejected). OPUS is best per second on greetings but poor on sentences. Decision: hybrid. Inputs of at most
  2 words use OPUS-MT, everything else NLLB. Caveats: the 10-phrase judgment is mine and small; MADLAD was timed on 8 sentences.
  Status: Decided. The MADLAD files remain in models/madlad-3b-ct2 (3 GB) for a possible GPU laptop.
- 2026-10-26 · Accurate (small) ASR got "Ողջույն" wrong ("Ողջուհին") on the user's clips while base heard it right. A text prompt of
  common greetings ("Բարև, ողջույն, շնորհակալություն, ինչպես ես, լավ եմ։") fixed it. Checked that it is not just leakage: on the user's
  7 read sentences (none contain those words) small WER went 45.1% -> 37.8%, CER 10.7% -> 9.5%; FLEURS(20) unchanged (30.1% -> 30.0%).
  The same prompt HURT base on FLEURS (29.8% -> 34.8%), so it is applied to the accurate model only. Caveat: one speaker, 7 sentences
  and ~5 greeting clips. Status: Decided.
- 2026-10-26 · Pre-roll raised from 0.13 s to 0.3 s. Evidence: on the user's 5 one-word clips (data/live6), 2 were already loud in
  the first 0.13 s (rms 0.13 to 0.15 at t=0), i.e. the first sound of the word was cut off before the VAD fired. The ASR mishears
  clipped onsets (Ո՞ւղջույն, Նշբես եք for Ինչպե՞ս եք). Not yet verified that it fixes the mishearing (no replay possible on already
  clipped audio). Also added the formal "ինչպես եք" to the accurate model's prompt. Mic noise floor is rms 0.04 vs speech 0.15 to 0.3
  (fan noise); a headset would likely help more. Status: Decided, unverified.
- 2026-10-26 · Short-phrase routing revised. The user's "Իսկ դուք" went to OPUS-MT under the 2-word rule and came out "And you are"
  (NLLB: "What about you?"). A 26-phrase check (`scripts/eval_phrases.py`, my own labels, indicative only): OPUS 18/26, NLLB 18/26, a
  tie by word count, but with complementary errors (OPUS: greetings right, junk like "TEPA" when unsure; NLLB the reverse).
  Tried a candidate reranker (both models score both models' top-2): 20/26, still wrong on Բարև; not adopted (complexity, headline
  case fails). Adopted: one-word inputs go to OPUS only if its mean token log-prob is >= -1.5 (junk scored -2.5 to -1.65, correct
  "Hi" -1.1 to -1.3), else NLLB; 2+ words always NLLB. Result 21/26. Caveat: the -1.5 threshold was chosen on the same 26 phrases,
  so real gains are likely smaller. Status: Decided.
- 2026-10-27 · Incident: "it doesn't get anything I say". The mic source had silently gone into a bad state: constant DC offset -0.38, rms 0.49,
  energy at 0 to 2 Hz, Silero VAD max probability 0.17 (no speech) over 20 s of the user talking. Earlier the same mic gave rms 0.03 to 0.1.
  Not a software bug; `pactl suspend-source <mic> 1; ... 0` (re-open the device) fixed it (mean -0.005, rms 0.029). Also found a stale
  second app instance (from an hour earlier) running at the same time, using 40% of RAM. Fix: `Session.start` now probes the mic for 1 s and
  fails loudly (DC offset > 0.1 or rms > 0.4) with the pactl command to run. Lesson: the earlier "mishearing" tests may partly have been
  made on a degraded mic; the live3 to live6 results (garbled words) should be rechecked now that the device is healthy. Status: Fixed.
- 2026-10-27 · Mic incident, revised diagnosis. Measured: at the sound card (arecord plughw, bypassing PulseAudio) the signal clips (peak 1.00, std 0.49)
  with a DC offset; through PulseAudio rms 0.49 constant. After a 100 Hz high-pass (kept: it removes the offset/drift) rms is still 0.27 to 0.43,
  broadband (80% of energy 300 Hz to 8 kHz): loud noise, not just drift. Silero VAD max probability rose from 0.17 (raw) to 0.84 (filtered) while
  the user talked, so speech is partly visible but buried. My first theory (PulseAudio 27% vs ALSA 92% gain mismatch) was WRONG: Pulse's
  27% = -34 dB re base -60 dB = +26 dB, which matches ALSA +26 dB; re-applying it changed the gain by 0.75 dB only (92% -> 90%). Cause not found in
  software; the same mic and settings were clean on previous days (rms 0.03 to 0.1). Candidates: loud environment, electrical noise/ground loop,
  codec stuck after 9+ days uptime. Mitigations: high-pass filter in the pipeline (permanent), startup check now fails loudly when filtered noise
  rms > 0.3 or > 1% samples clip, with hints. Status: Open (hardware/environment).
- 2026-10-27 · After `systemctl --user restart pulseaudio` (run by the user) the mic is still intermittent: 4 one-second probes gave rms 0.43 / 0.02 / 0.03 /
  0.47 and up to 10% clipping, so it alternates between clean and unusable within seconds. The startup check was changed from one 1 s probe to
  3 s judged in 0.5 s windows; it fails only if more than half the windows are saturated or noisy (3 of 3 real runs passed). Remaining risk: phrases that
  fall in a bad moment are lost. Status: Open (hardware). Next: reboot, or use a headset mic, then re-measure ASR accuracy on a healthy signal.
- 2026-10-27 · [RETRACTED, see next entry] Claimed root cause of the mic fault: AC adapter noise. After a reboot the mic was still bad on AC (28 of 29 seconds with raw rms > 0.2).
  Unplugging the charger (battery 100%) gave 16 of 18 clean seconds (rms 0.02 to 0.05, mean ~0); the 2 bad seconds were the power-source switch. Not
  gain, not PulseAudio, not drift. Everything measured about ASR accuracy on the user's voice between 2026-10-26 and 2026-10-27 (live3 to live9, the
  8 read sentences) was probably made on a noisy mic; those numbers (base WER 52.6% / CER 16.2%, small 45.1% / 10.7%) are pessimistic and must be re-measured
  on battery or with a headset. Mitigations kept: high-pass filter, startup mic check with a fix hint. Interview advice: run on battery or use a
  headset/USB mic. Status: Fixed (workaround).
- 2026-10-27 · Charger theory RETRACTED. About 10 minutes later, on battery with the app stopped, the mic was bad again (12 of 12 seconds with default latency;
  rms 0.45 to 0.50, peak 1.06) and also with --latency-msec=32. The earlier clean spell (16 of 18 s) was luck: the fault comes and goes, with clean
  stretches seen right after `pactl suspend-source` flips, a reboot-then-probe and the power switch. Not the charger, not the app, not gain (Pulse and
  ALSA gains agree), not drift (high-pass keeps rms 0.2 to 0.3). Hardware: Acer Aspire A515-54G, Realtek ALC255, snd_hda_intel `power_save=1`,
  `power_save_controller=Y`. Hypothesis to test (needs root): codec power-save causes the DC offset and noise bursts when it powers up; test with
  `echo 0 | sudo tee /sys/module/snd_hda_intel/parameters/power_save`. Other option: headset / USB mic. Status: Open.
- 2026-10-27 · Codec power-save hypothesis REJECTED. The user set `snd_hda_intel power_save=0` (verified by reading the parameter); the built-in mic was still
  bad for 26 of 29 seconds right after (rms 0.2 to 0.6, mean swinging -0.4 to 0). Ruled out: charger, app, gain, PulseAudio restart, reboot, codec power-save.
  The built-in analog input of this laptop is faulty or in a state software cannot clear. Decision: use an external microphone (wired headset on the 3.5 mm
  jack, USB mic, or a Bluetooth headset), `meetai --mic <source>`. Status: Open until an external mic is tested.
