"use client";

import { useCallback, useState } from "react";
import { Controls } from "@/components/Controls";
import { TranscriptView } from "@/components/TranscriptView";
import { useTranscript } from "@/lib/useTranscript";

export default function Home() {
  const { lines, running, connected, error } = useTranscript();
  const [localError, setLocalError] = useState<string | null>(null);
  const onError = useCallback((m: string) => setLocalError(m), []);
  const shown = localError ?? error;

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-8">
      <header className="flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold">meetAI</h1>
        <span className={connected ? "text-emerald-400" : "text-red-400"}>
          {connected ? "connected" : "disconnected"}
        </span>
      </header>
      <Controls running={running} onError={onError} />
      {shown && (
        <p role="alert" className="rounded bg-red-950 p-3 text-red-300">
          {shown}
        </p>
      )}
      <TranscriptView lines={lines} />
    </main>
  );
}
