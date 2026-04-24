import asyncio, re
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from config import Config
from database import db
@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "stats", "wait", "broadcast", "join", "me", "register", "referral", "chat"]))
async def chat_handler(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user or user.get('is_banned'): return
    config = await db.get_bot_settings()
    if not config.get('chat_enabled'): return
    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now(): return await message.reply(f"🔇 <b>You are MUTED.</b>\nExpiry: {user['chat_muted_until'].strftime('%H:%M %d/%m')}")
    has_link = any(ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK] for ent in (message.entities or []))
    if has_link or re.search(r"(http://|https://|\.com|\.net|\.org|\.me|t\.me)", message.text.lower()):
        await db.mute_user(user_id, Config.MUTE_DURATION_HOURS)
        return await message.reply(f"🚨 <b>LINK DETECTED!</b>\nYou are muted for {Config.MUTE_DURATION_HOURS} hours.")
    chat_text = f"👤 #<b>{user['nickname']}</b>\n\n{message.text}"
    active_users = await db.get_active_users()
    for target in active_users:
        if target['user_id'] == user_id: continue
        while True:
            try:
                await client.send_message(target['user_id'], chat_text)
                break
            except FloodWait as e: await asyncio.sleep(e.value + 3)
            except Exception: break
        await asyncio.sleep(0.05)
