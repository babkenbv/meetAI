#!/usr/bin/env bash
# Convert a Hugging Face Whisper checkpoint to a CTranslate2 int8 directory at models/asr.
# Usage: scripts/convert_asr.sh <hf-model-id> [output-dir]   e.g. scripts/convert_asr.sh Chillarmo/whisper-small-armenian-v2
# The tokenizer is taken from the checkpoint itself (BuzzASR replaces Whisper's tokenizer, so the stock
# openai tokenizer would give wrong token ids).
set -euo pipefail
MODEL="${1:?usage: convert_asr.sh <hf-model-id> [output-dir]}"
OUT="${2:-models/asr}"
ct2-transformers-converter --model "$MODEL" --output_dir "$OUT" \
  --quantization int8 --copy_files preprocessor_config.json --force
python - "$MODEL" "$OUT" <<'PY'
import sys
from transformers import WhisperTokenizerFast

WhisperTokenizerFast.from_pretrained(sys.argv[1]).backend_tokenizer.save(f"{sys.argv[2]}/tokenizer.json")
PY
