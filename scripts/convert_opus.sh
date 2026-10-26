#!/usr/bin/env bash
# Convert Helsinki-NLP/opus-mt-hy-en to CTranslate2 int8 at models/opus-hy-en-ct2 (tokenizer saved beside it).
set -euo pipefail
ct2-transformers-converter --model Helsinki-NLP/opus-mt-hy-en --output_dir models/opus-hy-en-ct2 \
  --quantization int8 --force
python - <<'PY'
from transformers import AutoTokenizer

AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-hy-en").save_pretrained("models/opus-hy-en-ct2")
PY
