import logging
from pyrogram import Client, filters
import config
from database import db
from utils import ref_keyboard

logger = logging.getLogger("REFERRAL")

@Client.on_message(filters.command(["referral", "refferal"]) & filters.private)
async def referral_cmd(client, message):
    bot_config = await db.get_bot_settings()
    if not bot_config.get('ref_system'): 
        return await message.reply("> ❌ <b>System alert</b>\n> \n> Referral system is currently disabled.")
        
    user = await db.get_user(message.from_user.id)
    if not user: return
    
    bot_info = client.me
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    
    await message.reply(
        f"> 👥 <b>Referral network</b>\n"
        f"> \n"
        f"> {bot_config.get('ref_text', '')}\n"
        f"> \n"
        f"> 🔗 <b>Your exclusive link:</b>\n"
        f"> <code>{ref_link}</code>\n"
        f"> \n"
        f"> 🪙 <b>Points:</b> {user['ref_balance']}/{bot_config['ref_count']}", 
        reply_markup=ref_keyboard(), 
        disable_web_page_preview=True
    )

@Client.on_message(filters.command("ref") & filters.user(config.Config.ADMIN_IDS))
async def ref_cmd_init(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> ⚙️ <b>Syntax error</b>\n> \n> Use format: <code>/ref on</code> or <code>/ref off</code>")
            
        if message.command[1].lower() == "off":
            await db.update_settings({"ref_system": False})
            return await message.reply("> ✅ <b>Referral system offline</b>\n> \n> Protocol successfully disabled.")
            
        config.admin_states[message.from_user.id] = {"step": "ref_1"}
        await message.reply("> 🔢 <b>Initiating setup</b>\n> \n> Enter the required number of referrals for a reward.")
    except Exception as e:
        logger.error(f"Referral admin command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")
