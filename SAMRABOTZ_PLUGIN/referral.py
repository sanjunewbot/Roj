from pyrogram import Client, filters
import config
from database import db, users
from utils import ref_keyboard, parse_duration

@Client.on_message(filters.command(["referral", "refferal"]) & filters.private)
async def referral_cmd(client, message):
    bot_config = await db.get_bot_settings()
    if not bot_config.get('ref_system'): return await message.reply("❌ Disabled.")
    user = await db.get_user(message.from_user.id)
    if not user: return
    bot_info = client.me
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    await message.reply(
        f"👥 <b>ℝ𝔼𝔽𝔼ℝℝ𝔸𝕃 ℕ𝔼𝕋𝕎𝕆ℝ𝕂</b>\n\n"
        f"{bot_config.get('ref_text', '')}\n\n"
        f"🔗 <code>{ref_link}</code>\n\n"
        f"🪙 ℙ𝕆𝕀ℕ𝕋𝕊: {user['ref_balance']}/{bot_config['ref_count']}", 
        reply_markup=ref_keyboard(), 
        disable_web_page_preview=True
    )

@Client.on_message(filters.command("ref") & filters.user(config.Config.ADMIN_IDS))
async def ref_cmd_init(client, message):
    try:
        if len(message.command) < 2: return await message.reply("⚙️ <b>Syntax:</b> `/ref on` or `/ref off`")
        if message.command[1].lower() == "off":
            await db.update_settings({"ref_system": False})
            return await message.reply("✅ <b>Referral System Offline.</b>")
        config.admin_states[message.from_user.id] = {"step": "ref_1"}
        await message.reply("🔢 <b>Initiating Setup:</b> Enter the required number of referrals for a reward.")
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.text & filters.user(config.Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "plans", "me", "register", "referral", "chat", "get_buttn", "tutorial"]) & ~filters.regex("^(GET MEDIA HISTORY)$"))
async def ref_admin_state_handler(client, message):
    uid = message.from_user.id
    if uid not in config.admin_states: return
    state = config.admin_states[uid]
    
    if state.get("step") == "ref_1":
        try:
            state["count"] = int(message.text)
            state["step"] = "ref_2"
            await message.reply("📝 <b>Step 2:</b> Provide the custom invitation text (HTML supported).")
        except ValueError: await message.reply("❌ <b>Invalid Input:</b> Please provide a numeric value.")
    elif state.get("step") == "ref_2":
        state["text"] = message.text
        state["step"] = "ref_3"
        await message.reply("⏱ <b>Final Step:</b> Provide the premium duration reward (e.g., 7d, 1M, 24h).")
    elif state.get("step") == "ref_3":
        if parse_duration(message.text):
            await db.update_settings({"ref_system": True, "ref_count": state["count"], "ref_text": state["text"], "ref_time_str": message.text})
            config.admin_states.pop(uid, None)
            await message.reply("✅ <b>Referral Protocol Configuration Complete. System is now active.</b>")
        else: await message.reply("❌ <b>Invalid Formatting:</b> Please utilize proper syntax (e.g., 7d, 1M).")
