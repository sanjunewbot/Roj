from pyrogram import Client, filters
from database import db
from utils import ref_keyboard
@Client.on_message(filters.command(["referral", "refferal"]) & filters.private)
async def referral_cmd(client, message):
    config = await db.get_bot_settings()
    if not config.get('ref_system'): return await message.reply("❌ Disabled.")
    user = await db.get_user(message.from_user.id)
    if not user: return
    bot_info = await client.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    await message.reply(f"👥 <b>Refer</b>\n\n{config.get('ref_text', '')}\n\n🔗 <code>{ref_link}</code>\n\n🪙 Points: {user['ref_balance']}/{config['ref_count']}", reply_markup=ref_keyboard(), disable_web_page_preview=True)
@Client.on_message(filters.command("ref") & filters.user(Config.ADMIN_IDS))
async def toggle_ref(client, message):
    from config import admin_states
    if len(message.command) < 2: return
    if message.command[1].lower() == "off":
        await db.update_settings({"ref_system": False})
        await message.reply("✅ OFF")
    else:
        admin_states[message.from_user.id] = {"step": "ref_1"}
        await message.reply("🔢 How many refers?")
