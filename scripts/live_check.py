"""Live smoke test: start a session, play one evaluation clip through the speakers, print what comes out.

Usage: python scripts/live_check.py [playback_delay_seconds]
Needs data/eval (scripts/fetch_eval.py). Plays sound on the default output for a few seconds.
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

from meetai.audio.devices import default_source
from meetai.config import Config
from meetai.format import format_line
from meetai.session import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
for noisy in ("speechbrain", "faster_whisper"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

delay = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
clip = Path("data/eval") / Path("data/eval/manifest.tsv").read_text().splitlines()[0].split("\t")[0]

session = Session(
    Config(), default_source("mic"), default_source("system"), [lambda line: print(format_line(line, True), flush=True)]
)
session.start()
print("session started", flush=True)
time.sleep(delay)
player = subprocess.Popen(["paplay", str(clip)])
deadline = time.time() + 20
try:
    while time.time() < deadline:
        session.check()
        time.sleep(0.3)
finally:
    player.wait()
    session.stop()
