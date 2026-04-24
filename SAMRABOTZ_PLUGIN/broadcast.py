import asyncio
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo # 🔥 Naye imports album ke liye
from pyrogram.errors import FloodWait, UserIsBlocked
from config import Config, media_queue
from database import db

async def broadcast_worker(bot: Client):
    while True:
        data = await media_queue.get()
        sender_id, messages = data['sender_id'], data['messages']
        user_info = await db.get_user(sender_id)
        config = await db.get_bot_settings()
        is_restricted = config.get('media_restriction', False)
        
        caption_text = f"👤 #<b>{user_info['nickname']}</b>\n✨ <b>Join ➠ @{Config.FORCE_SUB_CHANNEL}</b>"
        if config['pm_dlt']: caption_text += f"\n\n⏱ <i>Auto-Deletes in {config['dlt_time']}s!</i>"

        active_users = await db.get_active_users()
        print(f"📢 [BROADCAST] Queue processing. Found {len(active_users)} active users.")

        for target in active_users:
            if target['user_id'] == sender_id: 
                continue # Sender khudka media receive nahi karega
            
            while True:
                try:
                    protect = is_restricted and not target.get('is_premium', False)
                    
                    # 🔥 FIXED ALBUM (MEDIA GROUP) LOGIC 🔥
                    if len(messages) > 1:
                        media_list = []
                        for idx, m in enumerate(messages):
                            # Sirf pehli photo/video pe caption lagayenge
                            cap = caption_text if idx == 0 else ""
                            if m.photo:
                                media_list.append(InputMediaPhoto(m.photo.file_id, caption=cap))
                            elif m.video:
                                media_list.append(InputMediaVideo(m.video.file_id, caption=cap))
                        
                        if media_list:
                            # send_media_group protect_content support karta hai
                            sent = await bot.send_media_group(target['user_id'], media_list, protect_content=protect)
                    else:
                        sent = [await bot.copy_message(target['user_id'], sender_id, messages[0].id, caption=caption_text, protect_content=protect)]
                    
                    print(f"✅ [BROADCAST] Sent media to {target['user_id']}")
                    
                    if config['pm_dlt']:
                        async def dlt(cid, mids):
                            await asyncio.sleep(config['dlt_time'])
                            try: await bot.delete_messages(cid, mids)
                            except: pass
                        asyncio.create_task(dlt(target['user_id'], [m.id for m in sent]))

                    await asyncio.sleep(0.5) 
                    break # ✅ Message chala gaya, next pe jao
                
                except FloodWait as e:
                    wait_time = e.value + 3 
                    print(f"⏳ [BROADCAST] FloodWait! Holding for {wait_time}s. Will retry same user...")
                    await asyncio.sleep(wait_time)
                    
                except UserIsBlocked:
                    print(f"🚫 [BROADCAST] User {target['user_id']} blocked the bot. Removing from MongoDB.")
                    await db.remove_user(target['user_id'])
                    break
                    
                except Exception as e:
                    print(f"❌ [BROADCAST] Failed to send to {target['user_id']}: {e}")
                    break 
        
        if len(messages) == 1:
            print("⏱️ [BROADCAST] Single media sent. Waiting 60s for next broadcast...")
            await asyncio.sleep(60)
            
        media_queue.task_done()
        await asyncio.sleep(1)

@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_IDS) & filters.reply)
async def broadcast_cmd(client, message):
    b_msg = message.reply_to_message
    status_msg = await message.reply("⏳ <b>Broadcasting...</b>")
    sent = failed = deleted = 0
    all_users = await db.get_all_users()
    
    for u in all_users:
        while True:
            try:
                await b_msg.copy(u['user_id'])
                sent += 1
                break # ✅ Success
            except FloodWait as e:
                wait_time = e.value + 3
                await asyncio.sleep(wait_time)
            except UserIsBlocked:
                await db.remove_user(u['user_id'])
                deleted += 1
                break
            except Exception:
                failed += 1
                break
        await asyncio.sleep(0.05)
        
    await status_msg.edit_text(f"🏁 <b>Done!</b>\nSent: {sent} | Failed: {failed} | Deleted (From MongoDB): {deleted}")
