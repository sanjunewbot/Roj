from pyrogram import Client, filters
from config import Config, admin_states
from database import db
from utils import ref_keyboard

@Client.on_message(filters.command(["referral", "refferal"]) & filters.private)
async def referral_cmd(client, message):
    config = await db.get_bot_settings()
    if not config.get('ref_system'): return await message.reply("❌ Referral disabled.")
    user = await db.get_user(message.from_user.id)
    if not user: return
    
    bot_info = await client.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    await message.reply(f"👥 <b>Refer Get Premium</b>\n\n<i>{config.get('ref_text', '')}</i>\n\n🔗 <b>Link:</b>\n<code>{ref_link}</code>\n\n🪙 <b>Points:</b> <code>{user['ref_balance']} / {config['ref_count']}</code>", reply_markup=ref_keyboard(), disable_web_page_preview=True)

@Client.on_message(filters.command("ref") & filters.user(Config.ADMIN_IDS))
async def toggle_ref(client, message):
    if len(message.command) < 2: return await message.reply("⚙️ Usage: <code>/ref on</code> or <code>/ref off</code>")
    if message.command[1].lower() == "off":
        await db.update_settings({"ref_system": False})
        admin_states.pop(message.from_user.id, None)
        await message.reply("✅ Referral system 🔴 <b>OFF</b>")
    else:
        admin_states[message.from_user.id] = {"step": "ref_1"}
        await message.reply("⚙️ <b>Setup Step 1/3:</b>\nKitne refers chahiye reward ke liye? (Number)")
