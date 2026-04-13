from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.models.schemas import ChatSessionHistory, ChatSessionMessage


@dataclass
class SessionMemory:
    db_path: Path

    def __post_init__(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                create table if not exists messages (
                    session_id text not null,
                    role text not null,
                    content text not null,
                    created_at text not null
                )
                """
            )
            connection.commit()

    def append(self, session_id: str, role: str, content: str) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "insert into messages (session_id, role, content, created_at) values (?, ?, ?, ?)",
                (session_id, role, content, datetime.now(UTC).isoformat()),
            )
            connection.commit()

    def recent_context(self, session_id: str, limit: int = 4) -> str:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                select role, content from messages
                where session_id = ?
                order by rowid desc
                limit ?
                """,
                (session_id, limit),
            ).fetchall()
        rows.reverse()
        return "\n".join(f"{role}: {content}" for role, content in rows)

    def history(self, session_id: str) -> ChatSessionHistory:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                select role, content, created_at from messages
                where session_id = ?
                order by rowid asc
                """,
                (session_id,),
            ).fetchall()
        return ChatSessionHistory(
            session_id=session_id,
            messages=[
                ChatSessionMessage(role=role, content=content, created_at=created_at)
                for role, content, created_at in rows
            ],
        )
