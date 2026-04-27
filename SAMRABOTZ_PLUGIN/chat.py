import asyncio
import re
import time
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait

import config
from database import db

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "join", "me", "register", "referral", "chat", "get_buttn", "tutorial"]) & ~filters.regex("^(GET MEDIA HISTORY)$"))
async def chat_handler(client, message):
    user_id = message.from_user.id
    
    if user_id in config.admin_states:
        return
        
    user = await db.get_user(user_id)
    
    if not user or user.get('is_banned'):
        return
        
    bot_config = await db.get_bot_settings()
    
    if len(message.text) > 100:
        return await message.reply("⚠️ <b>Message limit exceeded!</b> You can only send up to 100 characters (including spaces).")
        
    now = time.time()
    history = config.chat_spam_tracker.get(user_id, [])
    history = [t for t in history if now - t < 30]
    
    if len(history) >= 3:
        return await message.reply("⏳ <b>Anti-Spam Active:</b> You sent 3 messages too quickly. Please wait 30 seconds.")
        
    history.append(now)
    config.chat_spam_tracker[user_id] = history
    
    if not bot_config.get('chat_enabled'):
        if user_id not in config.Config.ADMIN_IDS:
            return await message.reply("💬 <b>Global chat is currently OFF. The system is only accepting videos and photos.</b>")
        else:
            return await message.reply("💬 <b>System Alert:</b> Global chat is OFF. Regular users will receive a warning instead of their text being forwarded.")
            
    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now():
        return await message.reply(f"🔇 <b>ACCESS DENIED: You are currently muted.</b>\nRestriction lifts at: {user['chat_muted_until'].strftime('%H:%M %d/%m')}")
        
    if user_id not in config.Config.ADMIN_IDS:
        has_link = any(ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK, enums.MessageEntityType.MENTION, enums.MessageEntityType.CODE, enums.MessageEntityType.PRE] for ent in (message.entities or []))
        is_forward = getattr(message, "forward_origin", None) is not None
        
        if has_link or is_forward or re.search(r"(http://|https://|\.com|\.net|\.org|\.me|t\.me|@\w+)", message.text.lower()):
            await db.mute_user_time(user_id, config.Config.MUTE_PENALTY_MINUTES)
            return await message.reply(
                f"🚨 <b>SECURITY VIOLATION: UNAUTHORIZED LINK OR FORWARD DETECTED!</b>\n"
                f"Your account has been temporarily muted for {config.Config.MUTE_PENALTY_MINUTES} minutes. Sending and receiving media has been disabled."
            )
            
    chat_text = f"💬 #<b>{user['nickname']}</b>\n\n{message.text}"
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
