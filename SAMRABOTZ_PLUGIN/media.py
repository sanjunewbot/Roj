import asyncio, re
from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery
from pyrogram.errors import MessageNotModified
from datetime import datetime
from config import Config, media_queue, album_cache, RULES_TEXT
from database import db
from utils import get_time_left, start_keyboard, build_start_text, ref_keyboard, back_keyboard
@Client.on_message((filters.photo | filters.video) & filters.private)
async def handle_media(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user: return await message.reply("⚠️ /start bot.")
    if user.get('is_banned'): return
    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now(): return await message.reply(f"🔇 <b>You are MUTED.</b>\nExpiry: {user['chat_muted_until'].strftime('%H:%M %d/%m')}\nYou cannot send or receive media.")
    has_link = any(ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK, enums.MessageEntityType.MENTION, enums.MessageEntityType.CODE, enums.MessageEntityType.PRE] for ent in (message.caption_entities or []))
    is_forward = message.forward_date is not None or message.forward_from_chat is not None or message.forward_from is not None
    if has_link or is_forward or (message.caption and re.search(r"(http://|https://|\.com|\.net|\.org|\.me|t\.me|@\w+)", message.caption.lower())):
        await db.mute_user_time(user_id, Config.MUTE_PENALTY_MINUTES)
        return await message.reply(f"🚨 <b>LINK/FORWARD DETECTED IN CAPTION!</b>\nYou are muted for {Config.MUTE_PENALTY_MINUTES} minutes. Sending & Receiving Media Disabled.")
    uid = (message.photo or message.video).file_unique_id
    if await db.is_media_processed(uid): return await message.reply("❌ Duplicate!")
    await db.mark_media_processed(uid)
    bot_config = await db.get_bot_settings()
    if bot_config.get('bin_channel'):
        try: await message.copy(bot_config['bin_channel'])
        except: pass
    mid = message.media_group_id
    if mid:
        if mid not in album_cache:
            album_cache[mid] = []
            async def collect():
                await asyncio.sleep(3)
                await media_queue.put({'sender_id': user_id, 'messages': album_cache.pop(mid)})
                await db.update_activity(user_id)
                await client.send_message(user_id, "✅ Album Processed! +30m")
            asyncio.create_task(collect())
        album_cache[mid].append(message)
    else:
        await media_queue.put({'sender_id': user_id, 'messages': [message]})
        await db.update_activity(user_id)
        await message.reply("✅ Media Processed! +30m")
@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    user = await db.get_user(query.from_user.id)
    config = await db.get_bot_settings()
    try:
        if query.data == "show_rules": await query.message.edit_text(RULES_TEXT, reply_markup=back_keyboard())
        elif query.data == "show_status":
            if user.get('is_premium'): text = "⏳ <b>Time:</b> ♾️ Unlimited VIP"
            else: text = f"⏳ <b>Time:</b> {get_time_left(user['active_until'])}\n\n<i>Send media to increase!</i>"
            await query.message.edit_text(text, reply_markup=back_keyboard())
        elif query.data in ["back_start", "refresh_start"]: await query.message.edit_text(build_start_text(user), reply_markup=start_keyboard(config.get('ref_system')))
        elif query.data in ["show_referral", "refresh_ref"]:
            bot_info = await client.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['user_id']}"
            text = f"👥 <b>Refer</b>\n\n{config.get('ref_text', '')}\n\n🔗 <code>{ref_link}</code>\n\n🪙 Points: {user['ref_balance']}/{config['ref_count']}"
            await query.message.edit_text(text, reply_markup=ref_keyboard(), disable_web_page_preview=True)
    except MessageNotModified: pass
    except: pass
    try: await query.answer()
    except: pass
