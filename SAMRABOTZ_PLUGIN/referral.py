from pyrogram import Client, filters
from config import Config, admin_states
from database import db
from utils import ref_keyboard, parse_duration
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command(["referral", "refferal"]) & filters.private)
async def referral_cmd(client, message):
    config = await db.get_bot_settings()
    if not config.get('ref_system'): return await message.reply("❌ Referral disabled.")
    user = await db.get_user(message.from_user.id)
    if not user: return
    
    bot_info = await client.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    await message.reply(f"👥 <b>Refer Get Premium</b>\n\n🔗 <b>Link:</b>\n<code>{ref_link}</code>\n\n🪙 <b>Points:</b> <code>{user['ref_balance']} / {config['ref_count']}</code>", reply_markup=ref_keyboard())
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
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
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.text & filters.user(Config.ADMIN_IDS) & ~filters.command(["start", "ref", "binch", "broadcast", "me", "pmdlt", "wait", "add", "ban", "unban", "stats", "rem_prem", "restrict", "join", "help", "register", "referral"]))
async def admin_ref_handler(client, message):
    uid = message.from_user.id
    if uid not in admin_states: return
    state = admin_states[uid]
    
    if state.get("step") == "ref_1":
        state["count"], state["step"] = int(message.text), "ref_2"
        await message.reply("📝 <b>Step 2/3:</b> Custom invite text bhejo.")
    elif state.get("step") == "ref_2":
        state["text"], state["step"] = message.text.html, "ref_3"
        await message.reply("⏱ <b>Step 3/3:</b> Kitne time ka premium?\n(Format: <b>h</b>=hour, <b>d</b>=day, <b>M</b>=month)\ne.g., <code>5h</code>, <code>7d</code>, <code>1M</code>")
    elif state.get("step") == "ref_3":
        if not parse_duration(message.text): return await message.reply("❌ Invalid format. Use h, d, or M.")
        await db.update_settings({"ref_system": True, "ref_count": state["count"], "ref_text": state["text"], "ref_time_str": message.text})
        admin_states.pop(uid, None)
        await message.reply(f"✅ <b>Setup Complete!</b>\nPoints: {state['count']}\nTime: {message.text}")
        # ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------