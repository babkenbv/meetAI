"""PulseAudio / PipeWire (pulse-compatible) source discovery via `pactl`."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioDevice:
    index: int
    name: str
    is_monitor: bool  # a monitor source carries what the speakers play (the other side of a call)


def parse_sources(pactl_output: str) -> list[AudioDevice]:
    devices = []
    for line in pactl_output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        devices.append(AudioDevice(int(parts[0]), parts[1], parts[1].endswith(".monitor")))
    return devices


def list_sources() -> list[AudioDevice]:
    out = subprocess.run(
        ["pactl", "list", "short", "sources"], check=True, capture_output=True, text=True
    ).stdout
    return parse_sources(out)


def default_source(kind: str) -> str:
    """kind is 'mic' or 'system'. Returns the name of the default source of that kind."""
    sources = list_sources()
    if kind == "system":
        default_sink = subprocess.run(
            ["pactl", "get-default-sink"], check=True, capture_output=True, text=True
        ).stdout.strip()
        wanted = f"{default_sink}.monitor"
        for d in sources:
            if d.name == wanted:
                return d.name
        raise RuntimeError(f"No monitor source for default sink {default_sink!r}; pass --system explicitly")
    default_src = subprocess.run(
        ["pactl", "get-default-source"], check=True, capture_output=True, text=True
    ).stdout.strip()
    for d in sources:
        if d.name == default_src and not d.is_monitor:
            return d.name
    raise RuntimeError(f"Default source {default_src!r} is not a microphone; pass --mic explicitly")
