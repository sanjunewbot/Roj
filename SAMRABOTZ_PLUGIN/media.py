import asyncio
import time
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
import config
from database import db
from utils import get_time_left, start_keyboard, back_keyboard, ref_keyboard

logger = logging.getLogger("MEDIA")

invite_cache = {"url": None, "count": 10}
history_cooldowns = {}

@Client.on_message((filters.photo | filters.video) & filters.private)
async def handle_media(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user: 
        return await message.reply("> ⚠️ <b>System alert</b>\n> \n> You are not registered. Please run /start to initialize the bot.")
        
    if user.get('is_banned'): return
    
    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now(): 
        mute_time = user['chat_muted_until'].strftime('%H:%M %d/%m')
        return await message.reply(f"> 🔇 <b>Access denied: You are muted</b>\n> \n> Restriction lifts at: {mute_time}\n> <i>Transmission and reception of media files are disabled.</i>")
        
    media_obj = message.photo or message.video
    uid = media_obj.file_unique_id
    file_id = media_obj.file_id
    media_type = "photo" if message.photo else "video"
    
    if await db.is_media_processed(uid): 
        return await message.reply("> ❌ <b>Data error</b>\n> \n> Duplicate media detected.")
        
    file_number = await db.get_next_file_number()
    bot_info = client.me 
    bot_config = await db.get_bot_settings()
    
    try:
        if config.Config.FORCE_SUB_CHANNEL:
            fsub_id = int(config.Config.FORCE_SUB_CHANNEL) if str(config.Config.FORCE_SUB_CHANNEL).lstrip('-').isdigit() else config.Config.FORCE_SUB_CHANNEL
            chat_info = await client.get_chat(fsub_id)
            ch_name = chat_info.title
        else: ch_name = "Elite Private Vault"
    except Exception as e: 
        logger.warning(f"Could not fetch channel info, using default. Error: {str(e)}")
        ch_name = "Elite Private Vault"
        
    new_caption = (
        f"> 👤 <b>User:</b> #{user['nickname'].upper()}\n"
        f"> 📁 <b>File:</b> #{file_number}\n"
        f"> 📢 <b>Network:</b> {ch_name}\n"
        f"> 🤖 <b>Bot:</b> @{bot_info.username}"
    )
    if bot_config.get('pm_dlt'): 
        new_caption += f"\n> \n> ⚠️ <i>This media will auto-destruct in {bot_config.get('dlt_time', 60)} seconds.</i>"
        
    await db.save_media_to_history(file_id, media_type, uid, file_number, new_caption)
    await db.mark_media_processed(uid)
    message.caption = new_caption
    
    global invite_cache
    if invite_cache["count"] >= 10 or not invite_cache["url"]:
        try:
            if config.Config.FORCE_SUB_CHANNEL:
                fsub_id = int(config.Config.FORCE_SUB_CHANNEL) if str(config.Config.FORCE_SUB_CHANNEL).lstrip('-').isdigit() else config.Config.FORCE_SUB_CHANNEL
                link = await client.create_chat_invite_link(chat_id=fsub_id, member_limit=10)
                invite_cache["url"] = link.invite_link
                invite_cache["count"] = 0
        except Exception as e: 
            logger.error(f"Failed to generate invite link: {str(e)}", exc_info=True)
            
    invite_cache["count"] += 1
    
    btn_markup = None
    if invite_cache["url"]: 
        btn_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Network", url=invite_cache["url"])]])
        
    if bot_config.get('bin_channel'):
        try: 
            await message.copy(bot_config['bin_channel'], caption=new_caption, reply_markup=btn_markup)
        except Exception as e: 
            logger.error(f"Failed to copy media to bin channel {bot_config['bin_channel']}: {str(e)}", exc_info=True)
            
    mid = message.media_group_id
    if mid:
        if mid not in config.album_cache:
            config.album_cache[mid] = []
            async def collect():
                await asyncio.sleep(7)
                messages = config.album_cache.pop(mid, None)
                if messages:
                    await config.media_queue.put({'sender_id': user_id, 'messages': messages, 'markup': btn_markup})
                    await db.update_activity(user_id)
                    try: 
                        await client.send_message(user_id, "> ✅ <b>Media album processed successfully</b>\n> \n> Your time has been extended by 30 minutes.")
                    except Exception as e: 
                        logger.error(f"Failed to notify user {user_id} of album success: {str(e)}", exc_info=True)
            asyncio.create_task(collect())
        config.album_cache[mid].append(message)
    else:
        setattr(message, 'generated_markup', btn_markup)
        await config.media_queue.put({'sender_id': user_id, 'messages': [message], 'markup': btn_markup})
        await db.update_activity(user_id)
        await message.reply("> ✅ <b>Media processed successfully</b>\n> \n> Your time has been extended by 30 minutes.")

@Client.on_message(filters.text & filters.private & filters.regex("^(GET MEDIA HISTORY)$"))
async def reply_keyboard_handler(client, message):
    user_id = message.from_user.id
    now = time.time()
    
    if user_id in history_cooldowns:
        elapsed_time = now - history_cooldowns[user_id]
        if elapsed_time < 180:
            remaining = int(180 - elapsed_time)
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
            return await message.reply(f"> ⏳ <b>Anti-spam protocol active</b>\n> \n> Please wait <b>{time_str}</b> before requesting media history again.")
            
    user = await db.get_user(user_id)
    if not user: return
    
    bot_config = await db.get_bot_settings()
    if bot_config.get('get_btn_enabled'):
        history = await db.get_random_media_history(10)
        if not history: 
            return await message.reply("> 📭 <b>Empty archive</b>\n> \n> There is currently no media history available.")
            
        history_cooldowns[user_id] = now
        status_msg = await message.reply("> 🚀 <b>Fetching media history</b>\n> \n> <i>Please wait while data is retrieved...</i>")
        protect = bot_config.get('media_restriction', False) and not user.get('is_premium', False)
        
        global invite_cache
        if invite_cache["count"] >= 10 or not invite_cache["url"]:
            try:
                if config.Config.FORCE_SUB_CHANNEL:
                    fsub_id = int(config.Config.FORCE_SUB_CHANNEL) if str(config.Config.FORCE_SUB_CHANNEL).lstrip('-').isdigit() else config.Config.FORCE_SUB_CHANNEL
                    link = await client.create_chat_invite_link(chat_id=fsub_id, member_limit=10)
                    invite_cache["url"] = link.invite_link
                    invite_cache["count"] = 0
            except Exception as e: 
                logger.error(f"Failed to generate invite link for history: {str(e)}", exc_info=True)
                
        invite_cache["count"] += 1
        
        btn_markup = None
        if invite_cache["url"]: 
            btn_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Join Network", url=invite_cache["url"])]])
        bot_info = client.me
        
        try:
            if config.Config.FORCE_SUB_CHANNEL:
                fsub_id = int(config.Config.FORCE_SUB_CHANNEL) if str(config.Config.FORCE_SUB_CHANNEL).lstrip('-').isdigit() else config.Config.FORCE_SUB_CHANNEL
                chat_info = await client.get_chat(fsub_id)
                ch_name = chat_info.title
            else: ch_name = "Elite Private Vault"
        except Exception: 
            ch_name = "Elite Private Vault"
            
        for item in history:
            try:
                stored_cap = item.get('caption', "")
                f_num = item.get('file_number', 'N/A')
                
                new_cap = stored_cap if stored_cap else (
                    f"> 📁 <b>File:</b> #{f_num}\n"
                    f"> 📢 <b>Network:</b> {ch_name}\n"
                    f"> 🤖 <b>Bot:</b> @{bot_info.username}"
                )
                
                if item['type'] == "photo": 
                    await client.send_photo(message.from_user.id, item['file_id'], caption=new_cap, reply_markup=btn_markup, protect_content=protect)
                else: 
                    await client.send_video(message.from_user.id, item['file_id'], caption=new_cap, reply_markup=btn_markup, protect_content=protect)
                    
                await asyncio.sleep(0.5)
            except Exception as e: 
                logger.error(f"Failed to send history item {item.get('file_id')} to {message.from_user.id}: {str(e)}", exc_info=True)
                
        await status_msg.delete()

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    user = await db.get_user(query.from_user.id)
    bot_config = await db.get_bot_settings()
    try:
        if query.data == "show_rules":
            rules_text = (
                "> 📜 <b>Bot rules & guidelines</b>\n"
                "> \n"
                "> Share high-quality content you would love to receive. Keep the media flowing.\n"
                "> \n"
                "> ⚠️ <b>Strictly prohibited:</b>\n"
                "> • No offensive language or harassment\n"
                "> • No pedophilia or child abuse material (CP)\n"
                "> • No scamming or unauthorized promotions\n"
                "> • No obscene behavior or incest\n"
                "> • No animal pornography\n"
                "> • No unsolicited pictures of genitalia\n"
                "> \n"
                "> 🚨 <b>Penalty for violation: Permanent ban.</b>"
            )
            await query.message.edit_text(rules_text, reply_markup=back_keyboard())
        elif query.data == "show_status":
            if user.get('is_premium'): 
                text = "> ⏳ <b>Account time remaining</b>\n> \n> Unlimited VIP Status is currently active."
            else: 
                text = f"> ⏳ <b>Account time remaining</b>\n> \n> Remaining: {get_time_left(user['active_until'])}\n> \n> <i>Send media files to replenish your active time!</i>"
            await query.message.edit_text(text, reply_markup=back_keyboard())
        elif query.data in ["back_start", "refresh_start"]:
            time_val = "Unlimited VIP" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
            status_val = "VIP Premium" if user.get('is_premium') else "Standard Free"
            bot_info = client.me
            welcome_msg = (
                f"> 🔥 <b>Welcome to the elite network</b>\n"
                f"> \n"
                f"> Greetings, #{user['nickname'].upper()}! We are glad to have you here.\n"
                f"> \n"
                f"> 🤖 <b>Bot identity:</b> @{bot_info.username.upper()}\n"
                f"> ⚡ <b>System vibe:</b> Fast, secure, and advanced.\n"
                f"> \n"
                f"> ⏳ <b>Account time remaining:</b> {time_val}\n"
                f"> 💎 <b>Current status:</b> {status_val}\n"
                f"> \n"
                f"> 📩 <b>Join now:</b> <a href='https://t.me/roomjoinus'>@roomjoinus</a>"
            )
            await query.message.edit_text(welcome_msg, reply_markup=start_keyboard(bot_config.get('ref_system'), bot_config.get('tutorial_link')), disable_web_page_preview=True)
        elif query.data in ["show_referral", "refresh_ref"]:
            bot_info = client.me
            ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['user_id']}"
            text = (
                f"> 👥 <b>Referral network</b>\n"
                f"> \n"
                f"> {bot_config.get('ref_text', '')}\n"
                f"> \n"
                f"> 🔗 <b>Your exclusive link:</b>\n"
                f"> <code>{ref_link}</code>\n"
                f"> \n"
                f"> 🪙 <b>Points accumulated:</b> {user['ref_balance']}/{bot_config['ref_count']}"
            )
            await query.message.edit_text(text, reply_markup=ref_keyboard(), disable_web_page_preview=True)
    except MessageNotModified: 
        pass
    except Exception as e: 
        logger.error(f"Callback query processing failed: {str(e)}", exc_info=True)
        
    try: 
        await query.answer()
    except Exception as e: 
        logger.error(f"Failed to answer callback query: {str(e)}", exc_info=True)
