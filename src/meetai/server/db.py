"""PostgreSQL persistence. The schema is language-agnostic: every row carries its languages."""

from __future__ import annotations

import datetime as dt
import os

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session as DbSession, mapped_column

from meetai.types import Line


class Base(DeclarativeBase):
    pass


class SessionRow(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    src_lang: Mapped[str] = mapped_column(String(8))
    tgt_lang: Mapped[str] = mapped_column(String(8))


class UtteranceRow(Base):
    __tablename__ = "utterances"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    t_start: Mapped[float] = mapped_column(Float)
    t_end: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(16))
    speaker: Mapped[str] = mapped_column(String(64))
    src_lang: Mapped[str] = mapped_column(String(8))
    src_text: Mapped[str] = mapped_column(Text)
    tgt_lang: Mapped[str] = mapped_column(String(8))
    tgt_text: Mapped[str] = mapped_column(Text)
    latency_s: Mapped[float] = mapped_column(Float)


def make_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set (e.g. postgresql+psycopg://meetai:meetai@localhost:5432/meetai)")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def start_session(engine, src_lang: str, tgt_lang: str) -> int:
    with DbSession(engine) as db:
        row = SessionRow(started_at=now(), src_lang=src_lang, tgt_lang=tgt_lang)
        db.add(row)
        db.commit()
        return row.id


def end_session(engine, session_id: int) -> None:
    with DbSession(engine) as db:
        db.get(SessionRow, session_id).ended_at = now()
        db.commit()


def save_line(engine, session_id: int, line: Line) -> None:
    with DbSession(engine) as db:
        db.add(
            UtteranceRow(
                session_id=session_id,
                t_start=line.t_start,
                t_end=line.t_end,
                source=line.source.value,
                speaker=line.speaker,
                src_lang=line.src_lang,
                src_text=line.src_text,
                tgt_lang=line.tgt_lang,
                tgt_text=line.tgt_text,
                latency_s=line.latency_s,
            )
        )
        db.commit()


def list_sessions(engine) -> list[dict]:
    with DbSession(engine) as db:
        rows = db.scalars(select(SessionRow).order_by(SessionRow.id.desc())).all()
        return [
            {
                "id": r.id,
                "started_at": r.started_at.isoformat(),
                "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                "src_lang": r.src_lang,
                "tgt_lang": r.tgt_lang,
            }
            for r in rows
        ]


def session_lines(engine, session_id: int) -> list[dict]:
    with DbSession(engine) as db:
        rows = db.scalars(
            select(UtteranceRow).where(UtteranceRow.session_id == session_id).order_by(UtteranceRow.t_start)
        ).all()
        return [line_to_dict(r) for r in rows]


def line_to_dict(r) -> dict:
    return {
        "t_start": r.t_start,
        "t_end": r.t_end,
        "source": r.source,
        "speaker": r.speaker,
        "src_lang": r.src_lang,
        "src_text": r.src_text,
        "tgt_lang": r.tgt_lang,
        "tgt_text": r.tgt_text,
        "latency_s": r.latency_s,
    }
