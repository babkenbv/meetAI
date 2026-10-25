"use client";

import { useEffect, useState } from "react";
import { Device, getDevices, startSession, stopSession } from "@/lib/api";

export function Controls({ running, onError }: { running: boolean; onError: (m: string) => void }) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [mic, setMic] = useState("");
  const [system, setSystem] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getDevices().then(setDevices).catch((e) => onError(String(e)));
  }, [onError]);

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      onError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const select = (value: string, set: (v: string) => void, list: Device[], label: string) => (
    <label className="flex flex-col gap-1 text-sm text-neutral-400">
      {label}
      <select
        className="rounded bg-neutral-900 px-2 py-1.5 text-neutral-100"
        value={value}
        disabled={running}
        onChange={(e) => set(e.target.value)}
      >
        <option value="">Default</option>
        {list.map((d) => (
          <option key={d.name} value={d.name}>
            {d.name}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <div className="flex flex-wrap items-end gap-4">
      {select(mic, setMic, devices.filter((d) => !d.is_monitor), "Microphone")}
      {select(system, setSystem, devices.filter((d) => d.is_monitor), "System audio")}
      <button
        className="rounded bg-emerald-600 px-4 py-1.5 font-medium disabled:opacity-50"
        disabled={busy}
        onClick={() => act(() => (running ? stopSession() : startSession(mic || null, system || null)))}
      >
        {busy ? "Working…" : running ? "Stop" : "Start"}
      </button>
    </div>
  );
}
