import asyncio
import re
import time
import logging
from datetime import datetime
import aiohttp
from pyrogram import Client, filters, enums, ContinuePropagation
from pyrogram.errors import FloodWait

import config
from database import db

async def aio_reply(chat_id, text, reply_to=None):
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_to: payload["reply_to_message_id"] = reply_to
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as resp:
                if resp.status == 429:
                    r = await resp.json()
                    await asyncio.sleep(r.get("parameters", {}).get("retry_after", 3))
                    return await aio_reply(chat_id, text, reply_to)
                if resp.status != 200:
                    logging.getLogger("MAIN").error(f"Chat aio_reply Error: {await resp.text()}")
        except Exception as e:
            logging.getLogger("MAIN").error(f"Chat aio_reply Exception: {e}", exc_info=True)

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "plans", "me", "register", "referral", "chat", "get_buttn", "tutorial", "updatecmds", "cancel"]) & ~filters.regex("^(GET MEDIA HISTORY)$"), group=1)
async def chat_handler(client, message):
    user_id = message.from_user.id
    is_admin = user_id in config.Config.ADMIN_IDS

    if user_id in config.admin_states:
        raise ContinuePropagation

    if user_id in config.pending_payments:
        elapsed = time.time() - config.pending_payments[user_id]
        if elapsed < 300:
            return await aio_reply(
                user_id,
                "<blockquote>"
                "⚠️ <b>Invalid Input:</b> Please send a valid payment screenshot (Image) only."
                "</blockquote>",
                message.id
            )
        else:
            del config.pending_payments[user_id]

    user = await db.get_user(user_id)
    if not user or user.get('is_banned'): return

    bot_config = await db.get_bot_settings()

    if len(message.text) > 100 and not is_admin:
        return await aio_reply(
            user_id, 
            "<blockquote>"
            "⚠️ <b>Message limit exceeded!</b>\n"
            "You can only send up to 100 characters (including spaces)."
            "</blockquote>", 
            message.id
        )

    now = time.time()
    history = config.chat_spam_tracker.get(user_id, [])
    history = [t for t in history if now - t < 30]

    if len(history) >= 3 and not is_admin:
        return await aio_reply(
            user_id, 
            "<blockquote>"
            "⏳ <b>Anti-Spam Active:</b>\n"
            "You sent 3 messages too quickly. Please wait 30 seconds."
            "</blockquote>", 
            message.id
        )

    history.append(now)
    config.chat_spam_tracker[user_id] = history

    if not bot_config.get('chat_enabled'):
        if not is_admin:
            return await aio_reply(
                user_id, 
                "<blockquote>"
                "💬 <b>Global chat is currently OFF.</b>\n"
                "The system is only accepting videos and photos."
                "</blockquote>", 
                message.id
            )
        else:
            await aio_reply(
                user_id, 
                "<blockquote>"
                "💬 <b>System Alert:</b>\n"
                "Global chat is OFF. Regular users will receive a warning instead of their text being forwarded."
                "</blockquote>", 
                message.id
            )

    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now():
        return await aio_reply(
            user_id, 
            "<blockquote>"
            f"🔇 <b>ACCESS DENIED: You are currently muted.</b>\n"
            f"Restriction lifts at: {user['chat_muted_until'].strftime('%H:%M %d/%m')}"
            "</blockquote>", 
            message.id
        )

    if not is_admin:
        has_link = any(ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK, enums.MessageEntityType.MENTION, enums.MessageEntityType.CODE, enums.MessageEntityType.PRE] for ent in (message.entities or []))
        is_forward = getattr(message, "forward_origin", None) is not None

        if has_link or is_forward or re.search(r"(http://|https://|.com|.net|.org|.me|t.me|@w+)", message.text.lower()):
            await db.mute_user_time(user_id, config.Config.MUTE_PENALTY_MINUTES)
            logging.getLogger("MAIN").warning(f"User #{user['nickname']} muted for 2 mins due to link/forward violation.")
            return await aio_reply(
                user_id, 
                "<blockquote>"
                f"🚨 <b>SECURITY VIOLATION: UNAUTHORIZED LINK OR FORWARD DETECTED!</b>\n"
                f"Your account has been temporarily muted for {config.Config.MUTE_PENALTY_MINUTES} minutes."
                "</blockquote>", 
                message.id
            )

    display_name = config.Config.ADMIN_GOD_NAME if is_admin else f"#{user['nickname']}"

    target_nick = None
    if message.reply_to_message and message.reply_to_message.text:
        match = re.search(r"💬\s*#(\w+)", message.reply_to_message.text)
        if not match:
            match_god = re.search(config.Config.ADMIN_GOD_NAME, message.reply_to_message.text)
            if match_god: target_nick = config.Config.ADMIN_GOD_NAME
        else:
            target_nick = f"#{match.group(1)}"

    if target_nick:
        chat_text = f"💬 <b>{display_name}</b> ➦ <b>{target_nick}</b>\n\n{message.text}"
    else:
        chat_text = f"💬 <b>{display_name}</b>\n\n{message.text}"

    all_users = await db.get_all_users()

    for target in all_users:
        if target['user_id'] == user_id or target.get('is_banned') or (target.get('chat_muted_until') and target['chat_muted_until'] > datetime.now()):
            continue

        while True:
            try:
                await client.send_message(target['user_id'], chat_text)
                break
            except FloodWait as e:
                await asyncio.sleep(e.value + 3)
            except Exception:
                break
        await asyncio.sleep(0.05)
