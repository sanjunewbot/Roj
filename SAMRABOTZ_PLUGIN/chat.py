import asyncio
import logging
import re
import time
from datetime import datetime
from pyrogram import Client, filters, enums, ContinuePropagation
from pyrogram.errors import FloodWait

import config
from database import db

logger = logging.getLogger("CHAT")

@Client.on_message(filters.text & filters.private & filters.incoming & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "plans", "me", "register", "referral", "chat", "get_buttn", "tutorial", "updatecmds"]) & ~filters.regex("^(GET MEDIA HISTORY)$"), group=1)
async def chat_handler(client, message):
    user_id = message.from_user.id
    
    if user_id in config.admin_states:
        raise ContinuePropagation
        
    user = await db.get_user(user_id)
    
    if not user or user.get('is_banned'):
        return
        
    bot_config = await db.get_bot_settings()
    
    if len(message.text) > 100:
        return await message.reply("> ⚠️ <b>Message limit exceeded</b>\n> \n> You can only send up to 100 characters including spaces.")
        
    now = time.time()
    history = config.chat_spam_tracker.get(user_id, [])
    history = [t for t in history if now - t < 30]
    
    if len(history) >= 3:
        return await message.reply("> ⏳ <b>Anti-spam protocol active</b>\n> \n> You sent three messages too quickly. Please wait 30 seconds.")
        
    history.append(now)
    config.chat_spam_tracker[user_id] = history
    
    if not bot_config.get('chat_enabled'):
        if user_id not in config.Config.ADMIN_IDS:
            return await message.reply("> 💬 <b>Global chat offline</b>\n> \n> The system is currently only accepting videos and photos.")
        else:
            return await message.reply("> 💬 <b>System alert</b>\n> \n> Global chat is offline. Regular users will receive a warning instead of their text being forwarded.")
            
    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now():
        mute_time = user['chat_muted_until'].strftime('%H:%M %d/%m')
        return await message.reply(f"> 🔇 <b>Access denied: You are muted</b>\n> \n> Restriction lifts at: {mute_time}")
        
    if user_id not in config.Config.ADMIN_IDS:
        has_link = any(ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK, enums.MessageEntityType.MENTION, enums.MessageEntityType.CODE, enums.MessageEntityType.PRE] for ent in (message.entities or []))
        is_forward = getattr(message, "forward_origin", None) is not None
        
        if has_link or is_forward or re.search(r"(http://|https://|\.com|\.net|\.org|\.me|t\.me|@\w+)", message.text.lower()):
            await db.mute_user_time(user_id, config.Config.MUTE_PENALTY_MINUTES)
            return await message.reply(
                f"> 🚨 <b>Security violation: Unauthorized link or forward detected</b>\n"
                f"> \n"
                f"> Your account has been temporarily muted for {config.Config.MUTE_PENALTY_MINUTES} minutes. Sending and receiving media has been disabled."
            )
            
    target_nick = None
    if message.reply_to_message and message.reply_to_message.text:
        match = re.search(r"💬\s*#(\w+)", message.reply_to_message.text)
        if match:
            target_nick = match.group(1)

    if target_nick:
        chat_text = f"💬 #<b>{user['nickname']}</b> ➦ #<b>{target_nick}</b>\n\n{message.text}"
    else:
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
                logger.warning(f"FloodWait of {e.value}s encountered while sending chat from {user_id} to {target['user_id']}.")
                try:
                    await client.send_message(user_id, f"> ⚠️ <b>Message delivery delayed</b>\n> \n> Your message is experiencing a network delay.\n> <i>Approximate wait time: {e.value} seconds.</i>")
                except Exception:
                    pass
                await asyncio.sleep(e.value + 3)
            except Exception as e:
                logger.error(f"Failed to route chat message to {target['user_id']}: {str(e)}", exc_info=True)
                break
                
        await asyncio.sleep(0.05)
