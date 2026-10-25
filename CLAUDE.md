# meetAI project rules

- Goal and constraints: see `PLAN.md`. Decisions and their reasons: `DECISIONS.md`. Tests: `TESTS.md`.
- All AI processing is local. Never add cloud speech/translation APIs.
- Never commit model weights, audio recordings, or API keys. Keep them git-ignored.
- Fail loudly: no silent fallbacks, no swallowed exceptions, no speculative timeouts or extra features.
- Keep modules separate (audio, vad, speakers, asr, translate, pipeline/cli) with plain data in/out.
- Choose models only from measured numbers on this CPU-only machine; verify model names and library APIs against
  primary documentation before using them.
- Python 3.10; add dependencies deliberately. Commit small, one change at a time, only when the user asks.
- Update `DECISIONS.md` when a decision is made.
