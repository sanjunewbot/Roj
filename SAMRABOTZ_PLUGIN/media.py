import asyncio
import re
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery
from pyrogram.errors import MessageNotModified

import config
from database import db
from utils import get_time_left, start_keyboard, build_start_text, ref_keyboard, back_keyboard

@Client.on_message((filters.photo | filters.video) & filters.private)
async def handle_media(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user: return await message.reply("⚠️ You are not registered. Please run /start to initialize the bot.")
    if user.get('is_banned'): return
        
    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now():
        return await message.reply(
            f"🔇 <b>ACCESS DENIED: You are currently muted.</b>\n"
            f"Restriction lifts at: {user['chat_muted_until'].strftime('%H:%M %d/%m')}\n"
            "Transmission and reception of media files are disabled."
        )
        
    if user_id not in config.Config.ADMIN_IDS:
        has_link = any(ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK, enums.MessageEntityType.MENTION, enums.MessageEntityType.CODE, enums.MessageEntityType.PRE] for ent in (message.caption_entities or []))
        is_forward = message.forward_date is not None or message.forward_from_chat is not None or message.forward_from is not None
        
        if has_link or is_forward or (message.caption and re.search(r"(http://|https://|\.com|\.net|\.org|\.me|t\.me|@\w+)", message.caption.lower())):
            await db.mute_user_time(user_id, config.Config.MUTE_PENALTY_MINUTES)
            return await message.reply(
                f"🚨 <b>SECURITY VIOLATION: UNAUTHORIZED LINK DETECTED IN CAPTION!</b>\n"
                f"Your account has been temporarily muted for {config.Config.MUTE_PENALTY_MINUTES} minutes. Sending and receiving media has been disabled."
            )
            
    media_obj = message.photo or message.video
    uid = media_obj.file_unique_id
    file_id = media_obj.file_id
    media_type = "photo" if message.photo else "video"
    
    if await db.is_media_processed(uid): return await message.reply("❌ <b>Data Error: Duplicate media detected.</b>")
        
    await db.save_media_to_history(file_id, media_type, uid)
    await db.mark_media_processed(uid)
    
    bot_config = await db.get_bot_settings()
    
    if bot_config.get('bin_channel'):
        try: await message.copy(bot_config['bin_channel'])
        except: pass
            
    mid = message.media_group_id
    if mid:
        if mid not in config.album_cache:
            config.album_cache[mid] = []
            
            async def collect():
                await asyncio.sleep(7)
                messages = config.album_cache.pop(mid, None)
                if messages:
                    await config.media_queue.put({'sender_id': user_id, 'messages': messages})
                    await db.update_activity(user_id)
                    await client.send_message(user_id, "✅ <b>Media Album Processed Successfully!</b> Your time has been extended by 30 minutes.")
                
            asyncio.create_task(collect())
            
        config.album_cache[mid].append(message)
    else:
        await config.media_queue.put({'sender_id': user_id, 'messages': [message]})
        await db.update_activity(user_id)
        await message.reply("✅ <b>Media Processed Successfully!</b> Your time has been extended by 30 minutes.")

@Client.on_message(filters.text & filters.private & filters.regex("^(🎥 GET MEDIA HISTORY|📜 Rules|⏳ Status|👥 Referral Network|🔄 Refresh Dashboard|🔙 Back to Main Menu|🔄 Refresh Points)$"))
async def reply_keyboard_handler(client, message):
    user = await db.get_user(message.from_user.id)
    if not user: return
    
    bot_config = await db.get_bot_settings()
    text = message.text
    
    if text == "📜 Rules":
        await message.reply(config.RULES_TEXT, reply_markup=back_keyboard())
        
    elif text == "⏳ Status":
        if user.get('is_premium'): status_text = "⏳ <b>Account Time Remaining:</b> ♾️ Unlimited VIP Status"
        else: status_text = f"⏳ <b>Account Time Remaining:</b> {get_time_left(user['active_until'])}\n\n<i>Send media files to replenish your active time!</i>"
        await message.reply(status_text, reply_markup=back_keyboard())
        
    elif text in ["🔙 Back to Main Menu", "🔄 Refresh Dashboard"]:
        await message.reply(build_start_text(user), reply_markup=start_keyboard(bot_config.get('ref_system'), bot_config.get('get_btn_enabled')))
        
    elif text == "🎥 GET MEDIA HISTORY" and bot_config.get('get_btn_enabled'):
        history = await db.get_random_media_history(10)
        if not history:
            return await message.reply("📭 History me abhi koi video/photo nahi hai!")
            
        status_msg = await message.reply("🚀 Fetching media history...")
        
        for item in history:
            try:
                if item['type'] == "photo":
                    await client.send_photo(message.from_user.id, item['file_id'])
                else:
                    await client.send_video(message.from_user.id, item['file_id'])
            except Exception:
                pass
        await status_msg.delete()
        
    elif text in ["👥 Referral Network", "🔄 Refresh Points"]:
        bot_info = await client.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['user_id']}"
        ref_text = (
            f"👥 <b>Referral Network</b>\n\n"
            f"{bot_config.get('ref_text', '')}\n\n"
            f"🔗 <b>Your Exclusive Link:</b>\n<code>{ref_link}</code>\n\n"
            f"🪙 <b>Points Accumulated:</b> {user['ref_balance']}/{bot_config['ref_count']}"
        )
        await message.reply(ref_text, reply_markup=ref_keyboard(), disable_web_page_preview=True)