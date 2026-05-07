import asyncio
import time
import re
import aiohttp
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from pyrogram.errors import MessageNotModified
import config
from database import db
from utils import get_time_left, start_keyboard, back_keyboard, ref_keyboard, copy_raw_api_message, edit_raw_api_message

invite_cache = {"url": None, "count": 10}
history_cooldowns = {}

async def aio_reply(chat_id, text, reply_to=None):
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_to: payload["reply_to_message_id"] = reply_to
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json=payload)
        except Exception as e:
            logging.getLogger("MAIN").error(f"Media aio_reply Error: {e}", exc_info=True)

def create_action_buttons(invite_url, report_nick=None):
    keys = []
    if invite_url:
        keys.append([{"text": "𝕁𝕆𝕀ℕ ℕ𝔼𝕋𝕎𝕆ℝ𝕂", "url": invite_url, "style": "primary"}])
    if report_nick:
        keys.append([{"text": "🚨 ℝ𝔼ℙ𝕆ℝ𝕋", "callback_data": f"report_{report_nick}", "style": "danger"}])
    return {"inline_keyboard": keys} if keys else None

async def send_styled_media(chat_id, media_type, file_id, caption, protect_content, reply_markup):
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/{'sendPhoto' if media_type == 'photo' else 'sendVideo'}"
    payload = {
        "chat_id": chat_id,
        media_type: file_id,
        "caption": caption,
        "parse_mode": "HTML",
        "protect_content": protect_content
    }
    if reply_markup: payload["reply_markup"] = reply_markup
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status == 429:
                r = await resp.json()
                await asyncio.sleep(r.get("parameters", {}).get("retry_after", 3))
                return await send_styled_media(chat_id, media_type, file_id, caption, protect_content, reply_markup)

@Client.on_message((filters.photo | filters.video) & filters.private)
async def handle_media(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user: 
        return await aio_reply(
            user_id, 
            "<blockquote>"
            "⚠️ You are not registered. Please run /start to initialize the bot."
            "</blockquote>"
        )
    if user.get('is_banned'): return
    if user.get('chat_muted_until') and user['chat_muted_until'] > datetime.now(): 
        return await aio_reply(
            user_id, 
            "<blockquote>"
            f"🔇 <b>ACCESS DENIED: You are currently muted.</b>\n"
            f"Restriction lifts at: {user['chat_muted_until'].strftime('%H:%M %d/%m')}\n"
            f"Transmission and reception of media files are disabled."
            "</blockquote>"
        )

    media_obj = message.photo or message.video
    uid = media_obj.file_unique_id
    file_id = media_obj.file_id
    media_type = "photo" if message.photo else "video"
    if await db.is_media_processed(uid): 
        return await aio_reply(
            user_id, 
            "<blockquote>"
            "❌ <b>Data Error: Duplicate media detected.</b>"
            "</blockquote>"
        )

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
        f"👤 <b>𝕌𝕊𝔼ℝ:</b> #{user['nickname'].upper()}\n"
        f"📁 <b>𝔽𝕀𝕃𝔼:</b> #{file_number}\n"
        f"📢 <b>ℕ𝔼𝕋𝕎𝕆ℝ𝕂:</b> {ch_name}\n"
        f"🤖 <b>𝔹𝕆𝕋:</b> @{bot_info.username}"
    )
    if bot_config.get('pm_dlt'): 
        new_caption += f"\n\n⚠️ 𝕋ℍ𝕀𝕊 𝕄𝔼𝔻𝕀𝔸 𝕎𝕀𝕃𝕃 𝔹𝔼 𝔸𝕌𝕋𝕆-𝔻𝔼𝕊𝕋ℝ𝕌ℂ𝕋𝔼𝔻 𝕀ℕ {bot_config.get('dlt_time', 60)} 𝕊𝔼ℂ𝕆ℕ𝔻𝕊."

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

    raw_buttons = [[{"text": "𝕁𝕆𝕀ℕ ℕ𝔼𝕋𝕎𝕆ℝ𝕂", "url": invite_cache["url"], "style": "primary"}]] if invite_cache["url"] else None

    if config.Config.LOG_ID:
        try:
            log_cid = int(config.Config.LOG_ID) if str(config.Config.LOG_ID).lstrip('-').isdigit() else config.Config.LOG_ID
            res = await copy_raw_api_message(
                chat_id=log_cid,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=new_caption,
                buttons=raw_buttons
            )
            if res and not res.get("ok"):
                logging.getLogger("MEDIA").error(f"LOG_ID backup failed: {res}")
        except Exception as e:
            logging.getLogger("MEDIA").error(f"LOG_ID Exception: {e}", exc_info=True)

    mid = message.media_group_id
    if mid:
        if mid not in config.album_cache:
            config.album_cache[mid] = []
            async def collect():
                await asyncio.sleep(7)
                messages = config.album_cache.pop(mid, None)
                if messages:
                    await config.media_queue.put({'sender_id': user_id, 'messages': messages, 'invite_url': invite_cache["url"]})
                    await db.update_activity(user_id)
                    await aio_reply(
                        user_id, 
                        "<blockquote>"
                        "✅ <b>Media Album Processed Successfully!</b>\n"
                        "Your time has been extended by 30 minutes."
                        "</blockquote>"
                    )
            asyncio.create_task(collect())
        config.album_cache[mid].append(message)
    else:
        await config.media_queue.put({'sender_id': user_id, 'messages': [message], 'invite_url': invite_cache["url"]})
        await db.update_activity(user_id)
        await aio_reply(
            user_id, 
            "<blockquote>"
            "✅ <b>Media Processed Successfully!</b>\n"
            "Your time has been extended by 30 minutes."
            "</blockquote>"
        )

@Client.on_message(filters.text & filters.private & filters.regex("^(GET MEDIA HISTORY)$"))
async def reply_keyboard_handler(client, message):
    user_id = message.from_user.id
    is_admin = user_id in config.Config.ADMIN_IDS
    now = time.time()

    if user_id in history_cooldowns and not is_admin:
        elapsed_time = now - history_cooldowns[user_id]
        if elapsed_time < 180:
            remaining = int(180 - elapsed_time)
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
            return await aio_reply(
                user_id, 
                "<blockquote>"
                f"⏳ <b>Anti-Spam Protocol Active!</b>\n"
                "\n"
                f"Please wait <b>{time_str}</b> before requesting media history again."
                "</blockquote>"
            )

    user = await db.get_user(user_id)
    if not user: return

    bot_config = await db.get_bot_settings()
    if bot_config.get('get_btn_enabled'):
        history = await db.get_random_media_history(10)
        if not history: 
            return await aio_reply(
                user_id, 
                "<blockquote>"
                "📭 History me abhi koi video/photo nahi hai!"
                "</blockquote>"
            )

        history_cooldowns[user_id] = now
        await aio_reply(
            user_id, 
            "<blockquote>"
            "🚀 Fetching media history..."
            "</blockquote>"
        )
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

        bot_info = client.me
        try:
            if config.Config.FORCE_SUB_CHANNEL:
                chat_info = await client.get_chat(config.Config.FORCE_SUB_CHANNEL)
                ch_name = chat_info.title
            else: ch_name = "𝔼𝕃𝕀𝕋𝔼 ℙℝ𝕀𝕍𝔸𝕋𝔼 𝕍𝔸𝕌𝕃𝕋"
        except: ch_name = "𝔼𝕃𝕀𝕋𝔼 ℙℝ𝕀𝕍𝔸𝕋𝔼 𝕍𝔸𝕌𝕃𝕋"

        for item in history:
            try:
                stored_cap = item.get('caption', "")
                f_num = item.get('file_number', 'N/A')
                new_cap = stored_cap if stored_cap else (
                    f"📁 <b>𝔽𝕀𝕃𝔼:</b> #{f_num}\n📢 <b>ℕ𝔼𝕋𝕎𝕆ℝ𝕂:</b> {ch_name}\n🤖 <b>𝔹𝕆𝕋:</b> @{bot_info.username}"
                )

                match = re.search(r"#(.*?)(\n|$)", new_cap)
                report_nick = match.group(1).strip() if match else "Unknown"

                raw_markup = create_action_buttons(invite_cache["url"], report_nick)
                await send_styled_media(user_id, item['type'], item['file_id'], new_cap, protect, raw_markup)
                await asyncio.sleep(0.5)
            except Exception as e:
                logging.getLogger("MEDIA").error(f"Error fetching history media: {e}", exc_info=True)

@Client.on_callback_query(~filters.regex(r"^report_"))
async def cb_handler(client, query: CallbackQuery):
    user = await db.get_user(query.from_user.id)
    bot_config = await db.get_bot_settings()
    try:
        if query.data == "show_rules":
            rules_text = (
                "<blockquote>"
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
                "</blockquote>"
            )
            res = await edit_raw_api_message(query.message.chat.id, query.message.id, rules_text, back_keyboard())
            if res and not res.get("ok"): logging.getLogger("MEDIA").error(f"Rules Edit Failed: {res}")

        elif query.data == "show_status":
            if user.get('is_premium'): 
                text = (
                    "<blockquote>"
                    "⏳ <b>𝔸ℂℂ𝕆𝕌ℕ𝕋 𝕋𝕀𝕄𝔼 ℝ𝔼𝕄𝔸𝕀ℕ𝕀ℕ𝔾:</b> Unlimited VIP Status"
                    "</blockquote>"
                )
            else: 
                text = (
                    "<blockquote>"
                    f"⏳ <b>𝔸ℂℂ𝕆𝕌ℕ𝕋 𝕋𝕀𝕄𝔼 ℝ𝔼𝕄𝔸𝕀ℕ𝕀ℕ𝔾:</b> {get_time_left(user['active_until'])}\n\n"
                    "<i>Send media files to replenish your active time!</i>"
                    "</blockquote>"
                )
            res = await edit_raw_api_message(query.message.chat.id, query.message.id, text, back_keyboard())
            if res and not res.get("ok"): logging.getLogger("MEDIA").error(f"Status Edit Failed: {res}")

        elif query.data in ["back_start", "refresh_start"]:
            time_val = "𝕌ℕ𝕃𝕀𝕄𝕀𝕋𝔼𝔻" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now())).upper()
            status_val = "𝕍𝕀ℙ ℙℝ𝔼𝕄𝕀𝕌𝕄" if user.get('is_premium') else "𝕊𝕋𝔸ℕ𝔻𝔸ℝ𝔻 𝔽ℝ𝔼𝔼"
            bot_info = client.me
            welcome_msg = (
                "<blockquote>"
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
                "</blockquote>"
            )
            res = await edit_raw_api_message(query.message.chat.id, query.message.id, welcome_msg, start_keyboard(bot_config.get('ref_system'), bot_config.get('tutorial_link')))
            if res and not res.get("ok"): logging.getLogger("MEDIA").error(f"Menu Edit Failed: {res}")

        elif query.data in ["show_referral", "refresh_ref"]:
            bot_info = client.me
            ref_link = f"https://t.me/{bot_info.username}?start=ref_{user['user_id']}"
            text = (
                "<blockquote>"
                f"👥 <b>ℝ𝔼𝔽𝔼ℝℝ𝔸𝕃 ℕ𝔼𝕋𝕎𝕆ℝ𝕂</b>\n\n"
                f"{bot_config.get('ref_text', '')}\n\n"
                f"🔗 <b>𝕐𝕆𝕌ℝ 𝔼𝕏ℂ𝕃𝕌𝕊𝕀𝕍𝔼 𝕃𝕀ℕ𝕂:</b>\n<code>{ref_link}</code>\n\n"
                f"🪙 <b>ℙ𝕆𝕀ℕ𝕋𝕊 𝔸ℂℂ𝕌𝕄𝕌𝕃𝔸𝕋𝔼𝔻:</b> {user['ref_balance']}/{bot_config['ref_count']}"
                "</blockquote>"
            )
            res = await edit_raw_api_message(query.message.chat.id, query.message.id, text, ref_keyboard())
            if res and not res.get("ok"): logging.getLogger("MEDIA").error(f"Referral Edit Failed: {res}")

    except MessageNotModified: 
        pass
    except Exception as e: 
        logging.getLogger("MEDIA").error(f"Callback query exception: {e}", exc_info=True)
    try: 
        await query.answer()
    except Exception as e: 
        logging.getLogger("MEDIA").warning(f"Failed to answer callback query: {e}")
