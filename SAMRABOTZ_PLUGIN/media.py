import asyncio
import re
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, LinkPreviewOptions
from pyrogram.errors import MessageNotModified

import config
from database import db
from utils import get_time_left, start_keyboard, history_reply_keyboard, build_start_text, ref_keyboard, back_keyboard

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
            
    media_obj = message.photo or message.video
    uid = media_obj.file_unique_id
    file_id = media_obj.file_id
    media_type = "photo" if message.photo else "video"
    
    if await db.is_media_processed(uid): return await message.reply("❌ <b>Data Error: Duplicate media detected.</b>")
        
    file_number = await db.get_next_file_number()
    bot_info = await client.get_me()
    ch_name = config.Config.FORCE_SUB_CHANNEL if config.Config.FORCE_SUB_CHANNEL else "Our Network"
    
    new_caption = (
        f"📁 <b>File:</b> #{file_number}\n"
        f"📢 <b>Channel:</b> {ch_name}\n"
        f"🤖 <b>Bot:</b> @{bot_info.username}"
    )
    
    await db.save_media_to_history(file_id, media_type, uid, file_number, new_caption)
    await db.mark_media_processed(uid)
    
    message.caption = new_caption
    
    bot_config = await db.get_bot_settings()
    
    if bot_config.get('bin_channel'):
        try: await message.copy(bot_config['bin_channel'], caption=new_caption)
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

@Client.on_message(filters.text & filters.private & filters.regex("^(GET MEDIA HISTORY)$"))
async def reply_keyboard_handler(client, message):
    user = await db.get_user(message.from_user.id)
    if not user: return
    
    bot_config = await db.get_bot_settings()
    text = message.text
    
    if text == "GET MEDIA HISTORY" and bot_config.get('get_btn_enabled'):
        history = await db.get_random_media_history(10)
        if not history:
            return await message.reply("📭 History me abhi koi video/photo nahi hai!")
            
        status_msg = await message.reply("🚀 Fetching media history...")
        
        protect = bot_config.get('media_restriction', False) and not user.get('is_premium', False)
        
        for item in history:
            try:
                caption = item.get('caption', '')
                if item['type'] == "photo":
                    await client.send_photo(message.from_user.id, item['file_id'], caption=caption, protect_content=protect)
                else:
                    await client.send_video(message.from_user.id, item['file_id'], caption=caption, protect_content=protect)
            except Exception:
                pass
        await status_msg.delete()

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    user = await db.get_user(query.from_user.id)
    bot_config = await db.get_bot_settings()
    
    try:
        if query.data == "show_rules":
            await query.message.edit_text(config.RULES_TEXT, reply_markup=back_keyboard())
            
        elif query.data == "show_status":
            if user.get('is_premium'): text = "⏳ <b>Account Time Remaining:</b> Unlimited VIP Status"
            else: text = f"⏳ <b>Account Time Remaining:</b> {get_time_left(user['active_until'])}\n\n<i>Send media files to replenish your active time!</i>"
            await query.message.edit_text(text, reply_markup=back_keyboard())
            
        elif query.data in ["back_start", "refresh_start"]:
            await query.message.edit_text(
                build_start_text(user), 
                reply_markup=start_keyboard(bot_config.get('ref_system'), bot_config.get('tutorial_link'))
            )
            
        elif query.data in ["show_referral", "refresh_ref"]:
            bot_info = await client.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['user_id']}"
            text = (
                f"👥 <b>Referral Network</b>\n\n"
                f"{bot_config.get('ref_text', '')}\n\n"
                f"🔗 <b>Your Exclusive Link:</b>\n<code>{ref_link}</code>\n\n"
                f"🪙 <b>Points Accumulated:</b> {user['ref_balance']}/{bot_config['ref_count']}"
            )
            await query.message.edit_text(
                text, 
                reply_markup=ref_keyboard(), 
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
    except MessageNotModified: pass
    except Exception: pass
    try: await query.answer()
    except: pass
