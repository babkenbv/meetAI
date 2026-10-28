"""Detect another running meetAI process: two copies fight over the mic and the CPU and silently double the latency."""

from __future__ import annotations

import os
from pathlib import Path


def is_meetai_cli(cmdline: list[str]) -> bool:
    return "meetai.cli" in cmdline or (bool(cmdline) and Path(cmdline[0]).name == "meetai")


def other_instances(proc_root: str = "/proc", own_pid: int | None = None) -> list[int]:
    own_pid = os.getpid() if own_pid is None else own_pid
    found = []
    for entry in Path(proc_root).iterdir():
        if not entry.name.isdigit() or int(entry.name) == own_pid:
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes().split(b"\0")
        except OSError:  # the process ended while we were looking
            continue
        if is_meetai_cli([c.decode(errors="replace") for c in cmdline if c]):
            found.append(int(entry.name))
    return sorted(found)
