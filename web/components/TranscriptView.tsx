"use client";

import { useEffect, useRef } from "react";
import { Line } from "@/lib/api";

const clock = (s: number) => {
  const t = Math.floor(s);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(Math.floor(t / 3600))}:${p(Math.floor((t % 3600) / 60))}:${p(t % 60)}`;
};

export function TranscriptView({ lines }: { lines: Line[] }) {
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => end.current?.scrollIntoView({ behavior: "smooth" }), [lines.length]);

  if (lines.length === 0) return <p className="text-neutral-500">No speech yet.</p>;

  return (
    <ul className="flex flex-col gap-3">
      {lines.map((l, i) => (
        <li key={i} className="rounded bg-neutral-900 p-3">
          <div className="mb-1 flex items-center gap-2 text-xs text-neutral-400">
            <span>{clock(l.t_start)}</span>
            <span className={l.source === "mic" ? "text-sky-400" : "text-amber-400"}>{l.speaker}</span>
            <span>{l.latency_s.toFixed(1)}s</span>
          </div>
          <p lang={l.src_lang}>
            <span className="mr-2 text-xs uppercase text-neutral-500">{l.src_lang}</span>
            {l.src_text}
          </p>
          <p lang={l.tgt_lang} className="text-neutral-300">
            <span className="mr-2 text-xs uppercase text-neutral-500">{l.tgt_lang}</span>
            {l.tgt_text}
          </p>
        </li>
      ))}
      <div ref={end} />
    </ul>
  );
}
