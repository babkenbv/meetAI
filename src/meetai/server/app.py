"""FastAPI app: starts/stops a live session and streams lines to browsers over a WebSocket."""

from __future__ import annotations

import asyncio
import dataclasses
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from meetai.audio.devices import default_source, list_sources
from meetai.config import Config
from meetai.server import db
from meetai.types import Line


class StartRequest(BaseModel):
    mic: str | None = None
    system: str | None = None


def line_payload(line: Line) -> dict:
    d = dataclasses.asdict(line)
    d["source"] = line.source.value
    return {"type": "line", **d}


class Hub:
    """Fan-out of messages to connected WebSocket clients. Safe to call `publish` from any thread."""

    def __init__(self) -> None:
        self._clients: set[asyncio.Queue] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._clients.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._clients.discard(q)

    @property
    def client_count(self) -> int:
        return len(self._clients)

    def publish(self, message: dict) -> None:
        assert self._loop is not None
        self._loop.call_soon_threadsafe(self._fanout, message)

    def _fanout(self, message: dict) -> None:
        for q in self._clients:
            q.put_nowait(message)


def create_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or Config()
    hub = Hub()
    state: dict = {"session": None, "db_id": None, "monitor": None}
    engine = db.make_engine()

    async def monitor() -> None:
        """Surfaces background-thread failures to clients and stops the session."""
        while True:
            await asyncio.sleep(0.5)
            session = state["session"]
            if session is None:
                continue
            try:
                session.check()
            except BaseException as exc:
                hub.publish({"type": "error", "message": f"{type(exc).__name__}: {exc}"})
                await asyncio.to_thread(stop_session)

    def stop_session() -> None:
        session, db_id = state["session"], state["db_id"]
        if session is None:
            return
        state["session"] = state["db_id"] = None
        session.stop()
        db.end_session(engine, db_id)
        hub.publish({"type": "status", "running": False})

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        hub.bind(asyncio.get_running_loop())
        task = asyncio.create_task(monitor())
        yield
        task.cancel()
        await asyncio.to_thread(stop_session)

    app = FastAPI(title="meetAI", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"]
    )

    @app.get("/api/devices")
    def devices():
        return [dataclasses.asdict(d) for d in list_sources()]

    @app.get("/api/status")
    def status():
        return {"running": state["session"] is not None, "session_id": state["db_id"]}

    @app.post("/api/sessions")
    async def start(req: StartRequest):
        if state["session"] is not None:
            raise HTTPException(409, "A session is already running")
        from meetai.session import Session  # loads models

        mic = req.mic or default_source("mic")
        system = req.system or default_source("system")
        db_id = db.start_session(engine, cfg.src_lang, cfg.tgt_lang)

        def sink(line: Line) -> None:
            hub.publish(line_payload(line))
            db.save_line(engine, db_id, line)

        session = await asyncio.to_thread(Session, cfg, mic, system, [sink])
        await asyncio.to_thread(session.start)
        state["session"], state["db_id"] = session, db_id
        hub.publish({"type": "status", "running": True, "session_id": db_id})
        return {"session_id": db_id, "mic": mic, "system": system}

    @app.post("/api/sessions/stop")
    async def stop():
        await asyncio.to_thread(stop_session)
        return {"running": False}

    @app.get("/api/sessions")
    def sessions():
        return db.list_sessions(engine)

    @app.get("/api/sessions/{session_id}/lines")
    def lines(session_id: int):
        return db.session_lines(engine, session_id)

    @app.websocket("/ws")
    async def ws(socket: WebSocket):
        await socket.accept()
        q = hub.subscribe()

        async def send() -> None:
            await socket.send_json({"type": "status", "running": state["session"] is not None})
            while True:
                await socket.send_json(await q.get())

        async def watch_disconnect() -> None:
            while True:
                await socket.receive_text()  # raises WebSocketDisconnect when the client goes away

        tasks = [asyncio.create_task(send()), asyncio.create_task(watch_disconnect())]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for t in tasks:
                t.cancel()
            hub.unsubscribe(q)

    app.state.hub = hub
    return app
