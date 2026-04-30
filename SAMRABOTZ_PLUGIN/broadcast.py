import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from pyrogram.errors import FloodWait, UserIsBlocked
import config
from database import db
from utils import copy_raw_api_message

logger = logging.getLogger("BROADCAST")

class MockMessage:
    def __init__(self, msg_id):
        self.id = msg_id

async def broadcast_worker(bot: Client):
    while True:
        if config.media_queue is None:
            await asyncio.sleep(1)
            continue
            
        data = await config.media_queue.get()
        sender_id = data['sender_id']
        messages = data['messages']
        btn_markup = data.get('markup')
        
        user_info = await db.get_user(sender_id)
        
        if not user_info:
            logger.warning(f"Sender {sender_id} not found in database during broadcast.")
            config.media_queue.task_done()
            continue
            
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
                    if len(messages) > 1:
                        media_list = []
                        for idx, m in enumerate(messages):
                            cap = caption_text if idx == 0 else ""
                            if m.photo: media_list.append(InputMediaPhoto(m.photo.file_id, caption=cap))
                            elif m.video: media_list.append(InputMediaVideo(m.video.file_id, caption=cap))
                        if media_list: sent = await bot.send_media_group(target['user_id'], media_list, protect_content=protect)
                    else:
                        resp = await copy_raw_api_message(target['user_id'], sender_id, messages[0].id, caption=caption_text, buttons=btn_markup, protect_content=protect)
                        if resp and resp.get("ok"):
                            sent = [MockMessage(resp['result']['message_id'])]
                        else:
                            if resp:
                                err_code = resp.get("error_code")
                                if err_code == 429:
                                    raise FloodWait(value=resp.get("parameters", {}).get("retry_after", 3))
                                elif err_code == 403:
                                    raise UserIsBlocked()
                            sent = []
                        
                    if bot_config['pm_dlt'] and sent:
                        async def dlt(cid, mids):
                            await asyncio.sleep(bot_config['dlt_time'])
                            try: await bot.delete_messages(cid, mids)
                            except Exception as e: logger.error(f"Failed to delete messages for {cid}: {str(e)}", exc_info=True)
                        asyncio.create_task(dlt(target['user_id'], [m.id for m in sent]))
                        
                    await asyncio.sleep(0.05)
                    break
                except FloodWait as e:
                    logger.warning(f"FloodWait of {e.value}s encountered while broadcasting to {target['user_id']} from {sender_id}. Reason: Rapid requests.")
                    try:
                        await bot.send_message(sender_id, f"> ⚠️ <b>Network delay active</b>\n> \n> Your broadcast is experiencing a rate limit delay.\n> <i>Approximate wait time: {e.value} seconds.</i>")
                    except Exception:
                        pass
                    await asyncio.sleep(e.value + 3)
                except UserIsBlocked: 
                    await db.remove_user(target['user_id'])
                    break
                except Exception as e: 
                    logger.error(f"Unexpected error broadcasting to {target['user_id']}: {str(e)}", exc_info=True)
                    break
                
        if len(messages) == 1: await asyncio.sleep(2)
        config.media_queue.task_done()
        await asyncio.sleep(0.5)

@Client.on_message(filters.command("broadcast") & filters.user(config.Config.ADMIN_IDS))
async def broadcast_cmd(client, message):
    try:
        if not message.reply_to_message:
            return await message.reply("> 📢 <b>Instruction</b>\n> \n> Reply to a message or media to broadcast globally.")
            
        b_msg = message.reply_to_message
        status_msg = await message.reply("> ⏳ <b>Broadcasting in progress</b>\n> \n> <i>Please wait while the data stream is injected.</i>")
        sent = failed = deleted = 0
        all_users = await db.get_all_users()
        
        for u in all_users:
            while True:
                try:
                    await b_msg.copy(u['user_id'])
                    sent += 1
                    break
                except FloodWait as e: 
                    logger.warning(f"FloodWait of {e.value}s during global broadcast to {u['user_id']}.")
                    await asyncio.sleep(e.value + 3)
                except UserIsBlocked: 
                    await db.remove_user(u['user_id'])
                    deleted += 1
                    break
                except Exception as e: 
                    logger.error(f"Broadcast failed for {u['user_id']}: {str(e)}", exc_info=True)
                    failed += 1
                    break
            await asyncio.sleep(0.05)
            
        await status_msg.edit_text(f"> 🏁 <b>Broadcast complete</b>\n> \n> 🟢 Success: {sent}\n> 🔴 Failed: {failed}\n> 🗑️ Deleted: {deleted}")
    except Exception as e: 
        logger.error(f"Global broadcast command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")
