"use client";

import { useEffect, useState } from "react";
import { Line, ServerMessage, WS_URL } from "./api";

export function useTranscript() {
  const [lines, setLines] = useState<Line[]>([]);
  const [running, setRunning] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      const msg: ServerMessage = JSON.parse(ev.data);
      if (msg.type === "line") setLines((prev) => [...prev, msg]);
      else if (msg.type === "status") {
        setRunning(msg.running);
        if (msg.running) setError(null);
      } else setError(msg.message);
    };
    return () => ws.close();
  }, []);

  return { lines, running, connected, error, clear: () => setLines([]) };
}
