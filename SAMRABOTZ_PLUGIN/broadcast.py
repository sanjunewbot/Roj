import asyncio
from pyrogram import Client, filters
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
            try:
                protect = is_restricted and not target.get('is_premium', False)
                if len(messages) > 1:
                    sent = await bot.copy_media_group(target['user_id'], sender_id, messages[0].id, protect_content=protect)
                    try: await bot.edit_message_caption(target['user_id'], sent[0].id, caption=caption_text)
                    except: pass
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
            
            except FloodWait as e:
                print(f"⏳ [BROADCAST] FloodWait for {e.value}s. Sleeping...")
                await asyncio.sleep(e.value + 1)
            except Exception as e:
                print(f"❌ [BROADCAST] Failed to send to {target['user_id']}: {e}")
                continue
        
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
        try:
            await b_msg.copy(u['user_id'])
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            await b_msg.copy(u['user_id'])
            sent += 1
        except UserIsBlocked:
            await db.remove_user(u['user_id'])
            deleted += 1
        except: failed += 1
        await asyncio.sleep(0.05)
    await status_msg.edit_text(f"🏁 <b>Done!</b>\nSent: {sent} | Failed: {failed} | Deleted: {deleted}")
