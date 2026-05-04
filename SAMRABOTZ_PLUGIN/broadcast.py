import asyncio
import logging
import aiohttp
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from pyrogram.errors import FloodWait, UserIsBlocked
import config
from database import db

async def aio_copy_message(chat_id, from_chat_id, message_id, caption, protect_content, reply_markup):
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/copyMessage"
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
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
                return await aio_copy_message(chat_id, from_chat_id, message_id, caption, protect_content, reply_markup)
            if resp.status != 200:
                logging.getLogger("MAIN").error(f"Broadcast Copy Error: {await resp.text()}")
            return await resp.json()

def create_action_buttons(invite_url, report_nick):
    keys = []
    if invite_url:
        keys.append([{"text": "𝕁𝕆𝕀ℕ ℕ𝔼𝕋𝕎𝕆ℝ𝕂", "url": invite_url, "style": "primary"}])
    if report_nick:
        keys.append([{"text": "🚨 ℝ𝔼ℙ𝕆ℝ𝕋", "callback_data": f"report_{report_nick}", "style": "danger"}])
    return {"inline_keyboard": keys} if keys else None

async def broadcast_worker(bot: Client):
    while True:
        if config.media_queue is None:
            await asyncio.sleep(1)
            continue

        data = await config.media_queue.get()
        sender_id = data['sender_id']
        messages = data['messages']
        invite_url = data.get('invite_url')

        user_info = await db.get_user(sender_id)
        if not user_info:
            config.media_queue.task_done()
            continue

        raw_markup = create_action_buttons(invite_url, user_info['nickname'])
        bot_config = await db.get_bot_settings()
        is_restricted = bot_config.get('media_restriction', False)
        caption_text = messages[0].caption if messages[0].caption else ""

        active_users = await db.get_active_users()

        for target in active_users:
            if target['user_id'] == sender_id: continue
            if target.get('chat_muted_until') and target['chat_muted_until'] > datetime.now(): continue

            while True:
                try:
                    protect = is_restricted and not target.get('is_premium', False)
                    sent_ids = []
                    if len(messages) > 1:
                        media_list = []
                        for idx, m in enumerate(messages):
                            cap = caption_text if idx == 0 else ""
                            if m.photo: media_list.append(InputMediaPhoto(m.photo.file_id, caption=cap))
                            elif m.video: media_list.append(InputMediaVideo(m.video.file_id, caption=cap))
                        if media_list: 
                            sent = await bot.send_media_group(target['user_id'], media_list, protect_content=protect)
                            sent_ids = [m.id for m in sent]
                    else:
                        resp = await aio_copy_message(target['user_id'], sender_id, messages[0].id, caption_text, protect, raw_markup)
                        if resp and resp.get("ok"): sent_ids = [resp["result"]["message_id"]]

                    if bot_config['pm_dlt'] and sent_ids:
                        async def dlt(cid, mids):
                            await asyncio.sleep(bot_config['dlt_time'])
                            try: await bot.delete_messages(cid, mids)
                            except: pass
                        asyncio.create_task(dlt(target['user_id'], sent_ids))

                    await asyncio.sleep(0.05)
                    break
                except FloodWait as e: await asyncio.sleep(e.value + 3)
                except UserIsBlocked: await db.remove_user(target['user_id']); break
                except Exception as e: 
                    logging.getLogger("MAIN").error(f"Broadcast task error: {e}")
                    break

        if len(messages) == 1: await asyncio.sleep(2)
        config.media_queue.task_done()
        await asyncio.sleep(0.5)

@Client.on_message(filters.command("broadcast") & filters.user(config.Config.ADMIN_IDS))
async def broadcast_cmd(client, message):
    try:
        if not message.reply_to_message:
            return await message.reply(
                "<blockquote>"
                "📢 <b>Instruction:</b> Reply to a message or media to broadcast globally."
                "</blockquote>"
            )

        b_msg = message.reply_to_message
        status_msg = await message.reply(
            "<blockquote>"
            "⏳ <b>Broadcasting...</b>"
            "</blockquote>"
        )
        sent = failed = deleted = 0
        all_users = await db.get_all_users()

        for u in all_users:
            while True:
                try:
                    await b_msg.copy(u['user_id'])
                    sent += 1; break
                except FloodWait as e: await asyncio.sleep(e.value + 3)
                except UserIsBlocked: await db.remove_user(u['user_id']); deleted += 1; break
                except Exception: failed += 1; break
            await asyncio.sleep(0.05)

        await status_msg.edit_text(
            "<blockquote>"
            f"🏁 <b>Done!</b>\n\n"
            f"🟢 Success: {sent}\n"
            f"🔴 Failed: {failed}\n"
            f"🗑️ Deleted: {deleted}"
            "</blockquote>"
        )
    except Exception as e: 
        await message.reply(
            "<blockquote>"
            f"❌ <b>Fault:</b> {e}"
            "</blockquote>"
        )
