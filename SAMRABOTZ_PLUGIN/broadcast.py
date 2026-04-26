import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from pyrogram.errors import FloodWait, UserIsBlocked
import config
from database import db

async def broadcast_worker(bot: Client):
    while True:
        if config.media_queue is None:
            await asyncio.sleep(1)
            continue
            
        data = await config.media_queue.get()
        sender_id, messages = data['sender_id'], data['messages']
        user_info = await db.get_user(sender_id)
        
        # Bypass if user deleted account or is not in db to prevent crash
        if not user_info:
            config.media_queue.task_done()
            continue
            
        bot_config = await db.get_bot_settings()
        
        is_restricted = bot_config.get('media_restriction', False)
        caption_text = f"👤 #<b>{user_info['nickname']}</b>\n✨ <b>Join Network ➠ @{config.Config.FORCE_SUB_CHANNEL}</b>"
        
        if bot_config['pm_dlt']: caption_text += f"\n\n⏱ <i>Auto-destruct in {bot_config['dlt_time']}s!</i>"
        active_users = await db.get_active_users()
        
        for target in active_users:
            if target['user_id'] == sender_id: continue
            if target.get('chat_muted_until') and target['chat_muted_until'] > datetime.now(): continue
            
            while True:
                try:
                    protect = is_restricted and not target.get('is_premium', False)
                    if len(messages) > 1:
                        media_list = []
                        for idx, m in enumerate(messages):
                            cap = caption_text if idx == 0 else ""
                            if m.photo: media_list.append(InputMediaPhoto(m.photo.file_id, caption=cap))
                            elif m.video: media_list.append(InputMediaVideo(m.video.file_id, caption=cap))
                        if media_list: sent = await bot.send_media_group(target['user_id'], media_list, protect_content=protect)
                    else:
                        sent = [await bot.copy_message(target['user_id'], sender_id, messages[0].id, caption=caption_text, protect_content=protect)]
                        
                    if bot_config['pm_dlt']:
                        async def dlt(cid, mids):
                            await asyncio.sleep(bot_config['dlt_time'])
                            try: await bot.delete_messages(cid, mids)
                            except: pass
                        asyncio.create_task(dlt(target['user_id'], [m.id for m in sent]))
                        
                    await asyncio.sleep(0.05)
                    break
                except FloodWait as e: await asyncio.sleep(e.value + 3)
                except UserIsBlocked: await db.remove_user(target['user_id']); break
                except Exception: break
                
        if len(messages) == 1: await asyncio.sleep(2)
        config.media_queue.task_done()
        await asyncio.sleep(0.5)

@Client.on_message(filters.command("broadcast") & filters.user(config.Config.ADMIN_IDS))
async def broadcast_cmd(client, message):
    try:
        if not message.reply_to_message:
            return await message.reply("📢 <b>Instruction:</b> Reply to a message or media to broadcast globally.")
            
        b_msg = message.reply_to_message
        status_msg = await message.reply("⏳ <b>Broadcasting...</b>")
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
            
        await status_msg.edit_text(f"🏁 <b>Done!</b>\n\n🟢 Success: {sent}\n🔴 Failed: {failed}\n🗑️ Deleted: {deleted}")
    except Exception as e: await message.reply(f"❌ <b>Fault:</b> {e}")
