import random, re
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config, RULES_TEXT, JOIN_TEXT, admin_states
from database import db, users
from utils import check_fsub, parse_duration, build_start_text, start_keyboard, get_uptime
ADJECTIVES = ["Foggy", "Silent", "Hidden", "Dark", "Ghost", "Mystic", "Shadow", "Secret"]
NOUNS = ["Wolf", "Raven", "Sniper", "Hunter", "Storm", "Ninja", "Phantom", "Dragon"]
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    config = await db.get_bot_settings()
    user = await db.get_user(user_id)
    if not user and not config.get('registration_open', True): return await message.reply("🚫 <b>Registration Closed!</b>")
    if len(message.command) > 1 and message.command[1].startswith("ref_"):
        try:
            inviter_id = int(message.command[1].split("_")[1])
            if inviter_id != user_id and not user and config.get('ref_system'):
                await users.update_one({"user_id": inviter_id}, {"$inc": {"ref_balance": 1}})
                inviter = await db.get_user(inviter_id)
                try: await client.send_message(inviter_id, f"🎉 <b>New Referral!</b>\nPoints: {inviter['ref_balance']}/{config['ref_count']}")
                except: pass
                if inviter['ref_balance'] >= config['ref_count']:
                    duration = parse_duration(config['ref_time_str'])
                    if duration:
                        expiry = datetime.now() + duration
                        await users.update_one({"user_id": inviter_id}, {"$set": {"is_premium": True, "premium_expiry": expiry}, "$inc": {"ref_balance": -config['ref_count']}})
                        try: await client.send_message(inviter_id, "🎊 <b>Premium activated!</b>")
                        except: pass
        except: pass
    if not await check_fsub(client, user_id): return await message.reply("❌ <b>Access Denied!</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{Config.FORCE_SUB_CHANNEL}")]]))
    if not user:
        random_name = f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1000, 9999)}"
        await db.add_user(user_id, random_name)
        user = await db.get_user(user_id)
    await message.reply(build_start_text(user), reply_markup=start_keyboard(config.get('ref_system')), disable_web_page_preview=True)
@Client.on_message(filters.command("register") & filters.private)
async def register_cmd(client, message):
    if not await check_fsub(client, message.from_user.id): return
    if len(message.command) < 2: return await message.reply("📝 Usage: /register [name]")
    await users.update_one({"user_id": message.from_user.id}, {"$set": {"nickname": message.command[1]}})
    await message.reply(f"✅ Nickname changed to '<b>{message.command[1]}</b>'!")
@Client.on_message(filters.command("me") & filters.private)
async def me_cmd(client, message):
    user = await db.get_user(message.from_user.id)
    config = await db.get_bot_settings()
    if not user: return
    status = "👑 VIP Premium" if user.get('is_premium') else "🆓 Free Tier"
    text = f"📊 <b>Your Profile</b>\n👤 <b>Name:</b> <code>{user['nickname']}</code>\n⭐ <b>Account:</b> {status}\n📈 <b>Sent:</b> {user['total_sent']}\n👥 <b>Refs:</b> {user['ref_balance']}\n"
    if user.get('premium_expiry'): text += f"📅 <b>Expiry:</b> {user['premium_expiry'].strftime('%Y-%m-%d %H:%M')}"
    await message.reply(text)
@Client.on_message(filters.command("join") & filters.private)
async def join_cmd(client, message): await message.reply(JOIN_TEXT)
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    txt = "🛠 <b>Commands:</b>\n\n👤 /start, /register, /me, /referral, /join, /help"
    if message.from_user.id in Config.ADMIN_IDS: txt += "\n\n👑 /binch, /pmdlt, /add, /rem_prem, /restrict, /ref, /ban, /unban, /stats, /wait, /broadcast, /chat"
    await message.reply(txt)
@Client.on_message(filters.command("ban") & filters.user(Config.ADMIN_IDS))
async def ban_cmd(client, message):
    target_id, days = None, 365
    try:
        if message.reply_to_message and (message.reply_to_message.caption or message.reply_to_message.text):
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"👤 #<b>(.*?)</b>", content)
            if match:
                u = await db.get_user_by_nickname(match.group(1))
                if u: target_id = u['user_id']
            if len(message.command) > 1: days = int(message.command[1])
        elif len(message.command) >= 3:
            target_id, days = int(message.command[1]), int(message.command[2])
        if target_id:
            await db.ban_user(target_id, days)
            await message.reply(f"✅ User {target_id} banned for {days} days.")
            try: await client.send_message(target_id, f"🚨 <b>You have been BANNED for {days} days.</b>")
            except: pass
        else: await message.reply("❌ Reply to media or use: /ban [ID] [days]")
    except ValueError: await message.reply("❌ Invalid format. IDs and days must be numbers.")
@Client.on_message(filters.command("unban") & filters.user(Config.ADMIN_IDS))
async def unban_cmd(client, message):
    target_id = None
    try:
        if message.reply_to_message and (message.reply_to_message.caption or message.reply_to_message.text):
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"👤 #<b>(.*?)</b>", content)
            if match:
                u = await db.get_user_by_nickname(match.group(1))
                if u: target_id = u['user_id']
        elif len(message.command) >= 2: target_id = int(message.command[1])
        if target_id:
            await db.unban_user(target_id)
            await message.reply(f"✅ User {target_id} unbanned.")
        else: await message.reply("❌ Reply or use: /unban [ID]")
    except ValueError: await message.reply("❌ Invalid format. ID must be a number.")
@Client.on_message(filters.command("chat") & filters.user(Config.ADMIN_IDS))
async def toggle_chat(client, message):
    if len(message.command) < 2: return await message.reply("💬 /chat on/off")
    mode = message.command[1].lower() == "on"
    await db.update_settings({"chat_enabled": mode})
    await message.reply(f"💬 Global Chat: <b>{'ON' if mode else 'OFF'}</b>")
@Client.on_message(filters.command("stats") & filters.user(Config.ADMIN_IDS))
async def stats_cmd(client, message):
    t, a, b = await db.get_stats()
    await message.reply(f"📊 Total: {t} | Active: {a} | Banned: {b}\n⏱ Uptime: {get_uptime()}")
@Client.on_message(filters.command("rem_prem") & filters.user(Config.ADMIN_IDS))
async def rem_prem_cmd(client, message):
    admin_states[message.from_user.id] = {"step": "remove_premium_id"}
    await message.reply("🆔 Send User ID to remove premium.")
@Client.on_message(filters.command("restrict") & filters.user(Config.ADMIN_IDS))
async def restrict_cmd(client, message):
    if len(message.command) < 2: return
    mode = message.command[1].lower() == "on"
    await db.update_settings({"media_restriction": mode})
    await message.reply(f"✅ Restriction: {mode}")
@Client.on_message(filters.command("binch") & filters.user(Config.ADMIN_IDS))
async def set_bin(client, message):
    if len(message.command) < 2: return
    cid = int(message.command[1]) if message.command[1].lstrip('-').isdigit() else message.command[1]
    await db.update_settings({"bin_channel": cid})
    await message.reply(f"✅ Bin: {cid}")
@Client.on_message(filters.command("add") & filters.user(Config.ADMIN_IDS))
async def manual_add(client, message):
    if len(message.command) < 3: return
    dur = parse_duration(message.command[2])
    if dur:
        await users.update_one({"user_id": int(message.command[1])}, {"$set": {"is_premium": True, "premium_expiry": datetime.now() + dur}})
        await message.reply("✅ Added.")
@Client.on_message(filters.command("wait") & filters.user(Config.ADMIN_IDS))
async def wait_cmd(client, message):
    if len(message.command) < 2: return
    mode = message.command[1].lower() == "on"
    await db.update_settings({"registration_open": not mode})
    await message.reply(f"✅ Wait: {mode}")
@Client.on_message(filters.command("pmdlt") & filters.user(Config.ADMIN_IDS))
async def toggle_dlt(client, message):
    if len(message.command) < 2: return
    mode = message.command[1].lower() == "on"
    await db.update_settings({"pm_dlt": mode})
    if mode and len(message.command) >= 3: await db.update_settings({"dlt_time": int(message.command[2])})
    await message.reply(f"✅ Auto-Delete: {mode}")
@Client.on_message(filters.text & filters.user(Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "stats", "wait", "broadcast", "join", "me", "register", "referral", "chat"]))
async def admin_state_handler(client, message):
    uid = message.from_user.id
    if uid not in admin_states: return
    state = admin_states[uid]
    if state.get("step") == "remove_premium_id":
        try:
            target_id = int(message.text)
            await db.remove_premium(target_id)
            admin_states.pop(uid, None)
            await message.reply(f"✅ Removed: {target_id}")
            try: await client.send_message(target_id, "⚠️ <b>PREMIUM REMOVED BY ADMIN.</b>")
            except: pass
        except: pass
    elif state.get("step") == "ref_1":
        state["count"], state["step"] = int(message.text), "ref_2"
        await message.reply("📝 Send invite text.")
    elif state.get("step") == "ref_2":
        state["text"], state["step"] = message.text.html, "ref_3"
        await message.reply("⏱ Send duration (e.g. 7d).")
    elif state.get("step") == "ref_3":
        if parse_duration(message.text):
            await db.update_settings({"ref_system": True, "ref_count": state["count"], "ref_text": state["text"], "ref_time_str": message.text})
            admin_states.pop(uid, None)
            await message.reply("✅ Setup Done.")
