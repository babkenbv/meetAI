#!/usr/bin/env bash
# Convert NLLB-200 distilled 600M to a CTranslate2 int8 directory at models/nllb-600m-ct2.
set -euo pipefail
ct2-transformers-converter --model facebook/nllb-200-distilled-600M \
  --output_dir models/nllb-600m-ct2 --quantization int8 --force
# Keep the tokenizer next to the model so runtime needs no network.
python - <<'PY'
from transformers import AutoTokenizer

AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M").save_pretrained("models/nllb-600m-ct2")
PY
