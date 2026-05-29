"""
Server-side message queue for Hermes.

When Hermes is busy processing a turn, incoming messages from the user
are queued in SQLite (via SessionDB). When the current turn finishes,
queued messages are delivered in order.

This prevents message loss when users send multiple messages while
Hermes is still thinking.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_MAX_QUEUE_SIZE = 10  # max queued messages per session


class PendingMessageQueue:
    """SQLite-backed per-session message queue.

    Uses a ``pending_messages`` table in the Hermes SQLite store.
    Messages are inserted with a monotonically increasing seq and
    consumed in FIFO order.
    """

    def __init__(self, session_db: Any) -> None:
        self._db = session_db
        self._ensure_table()

    # -- schema ---------------------------------------------------------------

    def _ensure_table(self) -> None:
        try:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS pending_messages ("
                "  session_key TEXT NOT NULL,"
                "  seq INTEGER NOT NULL,"
                "  role TEXT NOT NULL DEFAULT 'user',"
                "  content TEXT NOT NULL,"
                "  ts REAL NOT NULL,"
                "  PRIMARY KEY (session_key, seq)"
                ")"
            )
            self._db.commit()
        except Exception as exc:
            logger.warning("pending_messages: could not create table: %s", exc)

    # -- public API -----------------------------------------------------------

    def enqueue(
        self,
        session_key: str,
        content: str,
        role: str = "user",
    ) -> bool:
        """Add a message to the queue. Returns False if queue is full."""
        try:
            count = self._db.execute(
                "SELECT COUNT(*) FROM pending_messages WHERE session_key = ?",
                (session_key,),
            ).fetchone()[0]
            if count >= _MAX_QUEUE_SIZE:
                logger.warning(
                    "pending_messages: queue full for %s (%d messages)",
                    session_key,
                    count,
                )
                return False

            self._db.execute(
                "INSERT INTO pending_messages (session_key, seq, role, content, ts) "
                "SELECT ?, IFNULL(MAX(seq), -1) + 1, ?, ?, ? "
                "FROM pending_messages WHERE session_key = ?",
                (session_key, role, content, time.time(), session_key),
            )
            self._db.commit()
            logger.info(
                "pending_messages: enqueued #%d for %s",
                count + 1,
                session_key,
            )
            return True
        except Exception as exc:
            logger.warning("pending_messages: enqueue failed: %s", exc)
            return False

    def drain(self, session_key: str) -> List[Dict[str, str]]:
        """Return and remove all queued messages for a session, in order."""
        try:
            rows = self._db.execute(
                "SELECT role, content FROM pending_messages "
                "WHERE session_key = ? ORDER BY seq ASC",
                (session_key,),
            ).fetchall()
            self._db.execute(
                "DELETE FROM pending_messages WHERE session_key = ?",
                (session_key,),
            )
            self._db.commit()
            return [{"role": r[0], "content": r[1]} for r in rows]
        except Exception as exc:
            logger.warning("pending_messages: drain failed: %s", exc)
            return []

    def count(self, session_key: str) -> int:
        """Return the number of queued messages for a session."""
        try:
            row = self._db.execute(
                "SELECT COUNT(*) FROM pending_messages WHERE session_key = ?",
                (session_key,),
            ).fetchone()
            return row[0] if row else 0
        except Exception as exc:
            logger.warning("pending_messages: count failed: %s", exc)
            return 0
