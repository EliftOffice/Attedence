"""Attendance Telegram bot (aiogram v3). Runs as a separate process/service.

Behaviour:
  /link <CODE>   (in DM)  -> captures the leader's Telegram id (user id == private
                            chat id) against the one-time code issued in the dashboard.
  group photo             -> resolve sender -> their BSG -> run recognition against
                            that group's members only -> save attendance + visitors
                            immediately -> reply with a MINIMAL confirmation
                            (NO visitor info in the group; visitors are reviewed in
                            the Angular app). Unregistered senders are ignored.

The bot deliberately downloads the photo to memory and never persists the full image.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import date

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.db.models import BibleStudyGroup
from app.db.session import SessionLocal
from app.services import config_store
from app.services.face.insightface_engine import decode_image, get_engine
from app.services.leader_resolver import (
    IncomingPhoto,
    link_leader_by_code,
    resolve_leader_from_message,
)
from app.services.recognition_pipeline import run_recognition

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("attendance-bot")

dp = Dispatcher()


@dp.message(Command("link"))
async def handle_link(message: Message) -> None:
    """DM link flow. A leader sends `/link <CODE>` privately to the bot."""
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Usage: /link <CODE>  (get the code from the dashboard)")
        return
    code = parts[1].strip().upper()
    db = SessionLocal()
    try:
        leader = link_leader_by_code(
            db,
            link_code=code,
            telegram_user_id=message.from_user.id,
            telegram_chat_id=message.chat.id,
        )
    finally:
        db.close()
    if leader:
        await message.reply(f"Linked! You are registered as leader of '{leader.bsg.name}'.")
    else:
        await message.reply("Invalid or already-used code.")


@dp.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    """A group photo posted by a leader. Largest available size is downloaded."""
    incoming = IncomingPhoto(
        sender_user_id=message.from_user.id, sender_chat_id=message.chat.id
    )
    db = SessionLocal()
    try:
        leader = resolve_leader_from_message(db, incoming)
        if leader is None:
            # OPEN DECISION: ignore (optionally inform). We inform once, politely.
            if config_store.get("telegram_reply_mode", db) != "silent":
                await message.reply("You are not a registered BSG leader; photo ignored.")
            return

        group = db.get(BibleStudyGroup, leader.bsg_id)

        # Download the largest photo size into memory (never stored to disk).
        photo = message.photo[-1]
        buf = await bot.download(photo.file_id)
        image_bytes = buf.read()

        # Reject stale photos (EXIF capture date too old) before recording attendance.
        max_age = int(float(config_store.get("max_photo_age_days", db)))
        reason = stale_reason(image_bytes, max_age)
        if reason:
            await message.reply(reason)
            return

        img = decode_image(image_bytes)

        result = run_recognition(
            db,
            engine=get_engine(),
            image_bgr=img,
            bsg=group,
            meeting_date=date.today(),
            source="telegram",
            persist=True,
        )
    except Exception:  # noqa: BLE001
        log.exception("Failed to process group photo")
        db.rollback()
        await message.reply("Sorry, something went wrong processing that photo.")
        return
    finally:
        db.close()

    await _reply_summary(message, bot, leader_chat_id=leader.telegram_chat_id, result=result)


async def _reply_summary(message: Message, bot: Bot, *, leader_chat_id, result) -> None:
    # Per product decision: do NOT post recognition counts in the group. Just
    # acknowledge and direct the leader to the dashboard to review attendance.
    text = (
        f"Photo received for {result.bsg_name}. "
        f"Please open the attendance dashboard to review and confirm."
    )
    mode = config_store.get("telegram_reply_mode") or "minimal"
    if mode == "silent":
        return
    if mode == "private" and leader_chat_id:
        await bot.send_message(leader_chat_id, text)
        return
    await message.reply(text)


async def _wait_for_token() -> str:
    """Block until a Telegram bot token is configured (in the DB settings or .env)."""
    while True:
        token = config_store.get("telegram_bot_token")
        if token:
            return token
        log.warning("No Telegram bot token set yet — set it in the admin dashboard. Waiting…")
        await asyncio.sleep(15)


async def _watch_token(current: str) -> None:
    """If an admin changes the token, exit so the container restarts with the new one
    (the bot service has restart: unless-stopped)."""
    while True:
        await asyncio.sleep(30)
        latest = config_store.get("telegram_bot_token")
        if latest and latest != current:
            log.info("Telegram token changed in settings — restarting bot.")
            os._exit(0)


async def main() -> None:
    token = await _wait_for_token()
    bot = Bot(token)
    asyncio.create_task(_watch_token(token))
    log.info("Attendance bot starting.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
