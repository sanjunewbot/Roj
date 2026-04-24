import asyncio
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from config import media_queue, album_cache, RULES_TEXT
from database import db
from utils import get_time_left, start_keyboard, build_start_text, ref_keyboard, back_keyboard
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message((filters.photo | filters.video) & filters.private)
async def handle_media(client, message):
    user_id = message.from_user.id
    if not await db.get_user(user_id): return await message.reply("⚠️ Please /start bot.")
    
    uid = (message.photo or message.video).file_unique_id
    if await db.is_media_processed(uid): return await message.reply("❌ <b>Duplicate Media!</b>")
    await db.mark_media_processed(uid)
    
    bot_config = await db.get_bot_settings()
    if bot_config.get('bin_channel'):
        try: await message.forward(bot_config['bin_channel'])
        except: pass
            
    mid = message.media_group_id
    if mid:
        if mid not in album_cache:
            album_cache[mid] = []
            async def collect():
                await asyncio.sleep(3)
                await media_queue.put({'sender_id': user_id, 'messages': album_cache.pop(mid)})
                await db.update_activity(user_id)
                await client.send_message(user_id, "✅ <b>Album Processed!</b> +30 mins added (Max 24h).")
            asyncio.create_task(collect())
        album_cache[mid].append(message)
    else:
        await media_queue.put({'sender_id': user_id, 'messages': [message]})
        await db.update_activity(user_id)
        await message.reply("✅ <b>Media Processed!</b> +30 mins added (Max 24h).")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    user = await db.get_user(query.from_user.id)
    config = await db.get_bot_settings()
    
    if query.data == "show_rules": 
        await query.message.edit_text(RULES_TEXT, reply_markup=back_keyboard())
        
    elif query.data == "show_status":
        # 🔥 Updated VIP Status UI
        if user.get('is_premium'):
            text = (
                "⏳ <b>Time:</b> ♾️ Unlimited Time\n\n"
                "👑 <b>VIP Premium Features:</b>\n"
                "✅ Unlimited Media Received\n"
                "✅ No Ads & Zero Delays\n"
                "✅ 24x7 Priority Support\n"
                "✅ Bypass Media Restrictions\n"
                "✅ VIP Group: 200k+ Content"
            )
        else:
            t = get_time_left(user['active_until'])
            text = f"⏳ <b>Time:</b> {t}\n\n<i>0 time = No receive. Send media to increase time!</i>"
        
        await query.message.edit_text(text, reply_markup=back_keyboard())
        
    elif query.data in ["back_start", "refresh_start"]: 
        await query.message.edit_text(build_start_text(user), reply_markup=start_keyboard(config.get('ref_system')))
        
    elif query.data == "show_referral":
        if not config.get('ref_system'): 
            return await query.answer("❌ Referral system is disabled.", show_alert=True)
        bot_info = await client.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['user_id']}"
        text = (f"👥 <b>Refer Get Premium</b>\n\n<i>{config.get('ref_text', '')}</i>\n\n"
                f"🔗 <b>Your Link:</b>\n<code>{ref_link}</code>\n\n"
                f"🪙 <b>Points:</b> <code>{user['ref_balance']} / {config['ref_count']}</code>")
        await query.message.edit_text(text, reply_markup=ref_keyboard(), disable_web_page_preview=True)
        
    elif query.data == "refresh_ref":
        if not config.get('ref_system'): 
            return await query.answer("❌ Referral system is disabled.", show_alert=True)
        bot_info = await client.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['user_id']}"
        text = (f"👥 <b>Refer Get Premium</b>\n\n<i>{config.get('ref_text', '')}</i>\n\n"
                f"🔗 <b>Your Link:</b>\n<code>{ref_link}</code>\n\n"
                f"🪙 <b>Points:</b> <code>{user['ref_balance']} / {config['ref_count']}</code>")
        try: await query.message.edit_text(text, reply_markup=ref_keyboard(), disable_web_page_preview=True)
        except: pass

    try: await query.answer()
    except: pass
    
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------    