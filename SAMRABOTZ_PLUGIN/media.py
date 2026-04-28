import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified
import config
from database import db
from utils import get_time_left, start_keyboard, back_keyboard, ref_keyboard

invite_cache = {"url": None, "count": 10}

@Client.on_message((filters.photo | filters.video) & filters.private)
async def handle_media(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user: return await message.reply("⚠️ You are not registered. Please run /start to initialize the bot.")
    if user.get('is_banned'): return
    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now(): return await message.reply(f"🔇 <b>ACCESS DENIED: You are currently muted.</b>\nRestriction lifts at: {user['chat_muted_until'].strftime('%H:%M %d/%m')}\nTransmission and reception of media files are disabled.")
    
    media_obj = message.photo or message.video
    uid = media_obj.file_unique_id
    file_id = media_obj.file_id
    media_type = "photo" if message.photo else "video"
    if await db.is_media_processed(uid): return await message.reply("❌ <b>Data Error: Duplicate media detected.</b>")
    
    file_number = await db.get_next_file_number()
    bot_info = client.me 
    bot_config = await db.get_bot_settings()
    
    try:
        if config.Config.FORCE_SUB_CHANNEL:
            chat_info = await client.get_chat(config.Config.FORCE_SUB_CHANNEL)
            ch_name = chat_info.title
        else: ch_name = "𝔼𝕃𝕀𝕋𝔼 ℙℝ𝕀𝕍𝔸𝕋𝔼 𝕍𝔸𝕌𝕃𝕋"
    except: ch_name = "𝔼𝕃𝕀𝕋𝔼 ℙℝ𝕀𝕍𝔸𝕋𝔼 𝕍𝔸𝕌𝕃𝕋"
    
    new_caption = (
        f"📁 <b>𝔽𝕀𝕃𝔼:</b> #{file_number}\n"
        f"📢 <b>ℕ𝔼𝕋𝕎𝕆ℝ𝕂:</b> {ch_name}\n"
        f"🤖 <b>𝔹𝕆𝕋:</b> @{bot_info.username}"
    )
    if bot_config.get('pm_dlt'): new_caption += f"\n\n⚠️ 𝕋ℍ𝕀𝕊 𝕄𝔼𝔻𝕀𝔸 𝕎𝕀𝕃𝕃 𝔹𝔼 𝔸𝕌𝕋𝕆-𝔻𝔼𝕊𝕋ℝ𝕌ℂ𝕋𝔼𝔻 𝕀ℕ {bot_config.get('dlt_time', 60)} 𝕊𝔼ℂ𝕆ℕ𝔻𝕊."
    
    await db.save_media_to_history(file_id, media_type, uid, file_number, new_caption)
    await db.mark_media_processed(uid)
    message.caption = new_caption
    
    global invite_cache
    if invite_cache["count"] >= 10 or not invite_cache["url"]:
        try:
            if config.Config.FORCE_SUB_CHANNEL:
                link = await client.create_chat_invite_link(chat_id=config.Config.FORCE_SUB_CHANNEL, member_limit=10)
                invite_cache["url"] = link.invite_link
                invite_cache["count"] = 0
        except Exception: pass
    invite_cache["count"] += 1
    
    btn_markup = None
    if invite_cache["url"]: btn_markup = InlineKeyboardMarkup([[InlineKeyboardButton("𝕁𝕆𝕀ℕ ℕ𝔼𝕋𝕎𝕆ℝ𝕂", url=invite_cache["url"])]])
    
    if bot_config.get('bin_channel'):
        try: await message.copy(bot_config['bin_channel'], caption=new_caption, reply_markup=btn_markup)
        except: pass
        
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
                    await client.send_message(user_id, "✅ <b>Media Album Processed Successfully!</b> Your time has been extended by 30 minutes.")
            asyncio.create_task(collect())
        config.album_cache[mid].append(message)
    else:
        setattr(message, 'generated_markup', btn_markup)
        # Fix: Now passing 'markup': btn_markup for single media too!
        await config.media_queue.put({'sender_id': user_id, 'messages': [message], 'markup': btn_markup})
        await db.update_activity(user_id)
        await message.reply("✅ <b>Media Processed Successfully!</b> Your time has been extended by 30 minutes.")

@Client.on_message(filters.text & filters.private & filters.regex("^(GET MEDIA HISTORY)$"))
async def reply_keyboard_handler(client, message):
    user = await db.get_user(message.from_user.id)
    if not user: return
    bot_config = await db.get_bot_settings()
    if bot_config.get('get_btn_enabled'):
        history = await db.get_random_media_history(10)
        if not history: return await message.reply("📭 History me abhi koi video/photo nahi hai!")
        status_msg = await message.reply("🚀 Fetching media history...")
        protect = bot_config.get('media_restriction', False) and not user.get('is_premium', False)
        
        global invite_cache
        if invite_cache["count"] >= 10 or not invite_cache["url"]:
            try:
                if config.Config.FORCE_SUB_CHANNEL:
                    link = await client.create_chat_invite_link(chat_id=config.Config.FORCE_SUB_CHANNEL, member_limit=10)
                    invite_cache["url"] = link.invite_link
                    invite_cache["count"] = 0
            except Exception: pass
        invite_cache["count"] += 1
        
        btn_markup = None
        if invite_cache["url"]: btn_markup = InlineKeyboardMarkup([[InlineKeyboardButton("𝕁𝕆𝕀ℕ ℕ𝔼𝕋𝕎𝕆ℝ𝕂", url=invite_cache["url"])]])
        bot_info = client.me
        
        try:
            if config.Config.FORCE_SUB_CHANNEL:
                chat_info = await client.get_chat(config.Config.FORCE_SUB_CHANNEL)
                ch_name = chat_info.title
            else: ch_name = "𝔼𝕃𝕀𝕋𝔼 ℙℝ𝕀𝕍𝔸𝕋𝔼 𝕍𝔸𝕌𝕃𝕋"
        except: ch_name = "𝔼𝕃𝕀𝕋𝔼 ℙℝ𝕀𝕍𝔸𝕋𝔼 𝕍𝔸𝕌𝕃𝕋"
        
        for item in history:
            try:
                f_num = item.get('file_number', 'N/A')
                new_cap = (
                    f"📁 <b>𝔽𝕀𝕃𝔼:</b> #{f_num}\n"
                    f"📢 <b>ℕ𝔼𝕋𝕎𝕆ℝ𝕂:</b> {ch_name}\n"
                    f"🤖 <b>𝔹𝕆𝕋:</b> @{bot_info.username}"
                )
                if bot_config.get('pm_dlt'): new_cap += f"\n\n⚠️ 𝕋ℍ𝕀𝕊 𝕄𝔼𝔻𝕀𝔸 𝕎𝕀𝕃𝕃 𝔹𝔼 𝔸𝕌𝕋𝕆-𝔻𝔼𝕊𝕋ℝ𝕌ℂ𝕋𝔼𝔻 𝕀ℕ {bot_config.get('dlt_time', 60)} 𝕊𝔼ℂ𝕆ℕ𝔻𝕊."
                if item['type'] == "photo": await client.send_photo(message.from_user.id, item['file_id'], caption=new_cap, reply_markup=btn_markup, protect_content=protect)
                else: await client.send_video(message.from_user.id, item['file_id'], caption=new_cap, reply_markup=btn_markup, protect_content=protect)
            except Exception: pass
        await status_msg.delete()

@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    user = await db.get_user(query.from_user.id)
    bot_config = await db.get_bot_settings()
    try:
        if query.data == "show_rules":
            rules_text = (
                "📜 <b>𝔹𝕆𝕋 ℝ𝕌𝕃𝔼𝕊 & 𝔾𝕌𝕀𝔻𝔼𝕃𝕀ℕ𝔼𝕊</b>\n\n"
                "Share high-quality content you would love to receive. Keep the media flowing.\n\n"
                "⚠️ <b>𝕊𝕋ℝ𝕀ℂ𝕋𝕃𝕐 ℙℝ𝕆ℍ𝕀𝔹𝕀𝕋𝔼𝔻:</b>\n"
                "• No offensive language or harassment\n"
                "• No pedophilia or child abuse material (CP)\n"
                "• No scamming or unauthorized promotions\n"
                "• No obscene behavior or incest\n"
                "• No animal pornography\n"
                "• No unsolicited pictures of genitalia\n\n"
                "🚨 <b>ℙ𝔼ℕ𝔸𝕃𝕋𝕐 𝔽𝕆ℝ 𝕍𝕀𝕆𝕃𝔸𝕋𝕀𝕆ℕ: ℙ𝔼ℝ𝕄𝔸ℕ𝔼ℕ𝕋 𝔹𝔸ℕ.</b>"
            )
            await query.message.edit_text(rules_text, reply_markup=back_keyboard())
        elif query.data == "show_status":
            if user.get('is_premium'): text = "⏳ <b>𝔸ℂℂ𝕆𝕌ℕ𝕋 𝕋𝕀𝕄𝔼 ℝ𝔼𝕄𝔸𝕀ℕ𝕀ℕ𝔾:</b> Unlimited VIP Status"
            else: text = f"⏳ <b>𝔸ℂℂ𝕆𝕌ℕ𝕋 𝕋𝕀𝕄𝔼 ℝ𝔼𝕄𝔸𝕀ℕ𝕀ℕ𝔾:</b> {get_time_left(user['active_until'])}\n\n<i>Send media files to replenish your active time!</i>"
            await query.message.edit_text(text, reply_markup=back_keyboard())
        elif query.data in ["back_start", "refresh_start"]:
            time_val = "𝕌ℕ𝕃𝕀𝕄𝕀𝕋𝔼𝔻" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now())).upper()
            status_val = "𝕍𝕀ℙ ℙℝ𝔼𝕄𝕀𝕌𝕄" if user.get('is_premium') else "𝕊𝕋𝔸ℕ𝔻𝔸ℝ𝔻 𝔽ℝ𝔼𝔼"
            bot_info = client.me
            welcome_msg = (
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🔥 𝕎𝔼𝕃ℂ𝕆𝕄𝔼 𝕋𝕆 𝕋ℍ𝔼 𝔼𝕃𝕀𝕋𝔼 ℕ𝔼𝕋𝕎𝕆ℝ𝕂 🔥\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"𝔾ℝ𝔼𝔼𝕋𝕀ℕ𝔾𝕊, #{user['nickname'].upper()}! 𝕎𝔼 𝔸ℝ𝔼 𝔾𝕃𝔸𝔻 𝕋𝕆 ℍ𝔸𝕍𝔼 𝕐𝕆𝕌 ℍ𝔼ℝ𝔼.\n\n"
                f"🤖 𝔹𝕆𝕋 𝕀𝔻𝔼ℕ𝕋𝕀𝕋𝕐: @{bot_info.username.upper()}\n"
                "⚡ 𝕊𝕐𝕊𝕋𝔼𝕄 𝕍𝕀𝔹𝔼: 𝔽𝔸𝕊𝕋, 𝕊𝔼ℂ𝕌ℝ𝔼, 𝔸ℕ𝔻 𝔸𝔻𝕍𝔸ℕℂ𝔼𝔻.\n\n"
                f"⏳ 𝔸ℂℂ𝕆𝕌ℕ𝕋 𝕋𝕀𝕄𝔼 ℝ𝔼𝕄𝔸𝕀ℕ𝕀ℕ𝔾: {time_val}\n"
                f"💎 ℂ𝕌ℝℝ𝔼ℕ𝕋 𝕊𝕋𝔸𝕋𝕌𝕊: {status_val}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "📩 𝕁𝕆𝕀ℕ ℕ𝕆𝕎: <a href='https://t.me/roomjoinus'>@roomjoinus</a>"
            )
            await query.message.edit_text(welcome_msg, reply_markup=start_keyboard(bot_config.get('ref_system'), bot_config.get('tutorial_link')), disable_web_page_preview=True)
        elif query.data in ["show_referral", "refresh_ref"]:
            bot_info = client.me
            ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['user_id']}"
            text = (
                f"👥 <b>ℝ𝔼𝔽𝔼ℝℝ𝔸𝕃 ℕ𝔼𝕋𝕎𝕆ℝ𝕂</b>\n\n"
                f"{bot_config.get('ref_text', '')}\n\n"
                f"🔗 <b>𝕐𝕆𝕌ℝ 𝔼𝕏ℂ𝕃𝕌𝕊𝕀𝕍𝔼 𝕃𝕀ℕ𝕂:</b>\n<code>{ref_link}</code>\n\n"
                f"🪙 <b>ℙ𝕆𝕀ℕ𝕋𝕊 𝔸ℂℂ𝕌𝕄𝕌𝕃𝔸𝕋𝔼𝔻:</b> {user['ref_balance']}/{bot_config['ref_count']}"
            )
            await query.message.edit_text(text, reply_markup=ref_keyboard(), disable_web_page_preview=True)
    except MessageNotModified: pass
    except Exception: pass
    try: await query.answer()
    except: pass
