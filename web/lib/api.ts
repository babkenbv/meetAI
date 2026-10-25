export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const WS_URL = API.replace(/^http/, "ws") + "/ws";

export type Line = {
  type: "line";
  t_start: number;
  t_end: number;
  source: "mic" | "system";
  speaker: string;
  src_lang: string;
  src_text: string;
  tgt_lang: string;
  tgt_text: string;
  latency_s: number;
};

export type ServerMessage =
  | Line
  | { type: "status"; running: boolean; session_id?: number }
  | { type: "error"; message: string };

export type Device = { index: number; name: string; is_monitor: boolean };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API + path, { ...init, headers: { "Content-Type": "application/json" } });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const getDevices = () => request<Device[]>("/api/devices");
export const startSession = (mic: string | null, system: string | null) =>
  request<{ session_id: number }>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ mic, system }),
  });
export const stopSession = () => request<{ running: boolean }>("/api/sessions/stop", { method: "POST" });
