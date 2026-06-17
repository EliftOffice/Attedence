"""Telegram identity resolution — ISOLATED here (OPEN DECISION #5).

We match the SENDER of a group message against BSGLeaders. By default we match on
the Telegram *user id* (`message.from.id`), which equals the user's private chat id
captured during the bot-DM link flow, and is also what appears as the sender on a
GROUP message. To switch to matching on a stored chat id instead, change
`settings.telegram_match_field` to "chat_id" — this is the ONLY place that branches.

TODO: confirm against a real group message that `from.id` is the value stored in
bsg_leaders.telegram_user_id before going to production.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import BSGLeader
from app.services import config_store


@dataclass
class IncomingPhoto:
    sender_user_id: int  # message.from.id
    sender_chat_id: int  # message.chat.id (the group's id for a group message)


def resolve_leader_from_message(db: Session, msg: IncomingPhoto) -> BSGLeader | None:
    """Return the BSGLeader for the message sender, or None if not a registered leader.
    The match field (user_id vs chat_id) is admin-configurable (OPEN DECISION #5)."""
    if config_store.get("telegram_match_field", db) == "chat_id":
        key = msg.sender_chat_id
        return db.scalar(select(BSGLeader).where(BSGLeader.telegram_chat_id == key))
    # default: user_id
    key = msg.sender_user_id
    return db.scalar(select(BSGLeader).where(BSGLeader.telegram_user_id == key))


def link_leader_by_code(
    db: Session, *, link_code: str, telegram_user_id: int, telegram_chat_id: int
) -> BSGLeader | None:
    """DM link flow: a leader sends their one-time code to the bot. We capture the
    real ids from that DM (private chat id == user id) and clear the code."""
    from datetime import datetime, timezone

    leader = db.scalar(select(BSGLeader).where(BSGLeader.telegram_link_code == link_code))
    if leader is None:
        return None
    leader.telegram_user_id = telegram_user_id
    leader.telegram_chat_id = telegram_chat_id
    leader.telegram_link_code = None
    leader.telegram_linked_at = datetime.now(timezone.utc)
    db.commit()
    return leader
