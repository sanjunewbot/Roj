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
    if len(message.command) < 2: return await message.reply("📝 Usage: `/register [name]`")
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
    txt = "🛠 <b>BOT COMMAND CENTER</b>\n\n<b>👤 USER COMMANDS:</b>\n🚀 <code>/start</code> - Dashboard\n🎭 <code>/register [name]</code> - Change Name\n📊 <code>/me</code> - Check Profile\n👥 <code>/referral</code> - Get Premium\n💎 <code>/join</code> - VIP Benefits\n"
    if message.from_user.id in Config.ADMIN_IDS: txt += "\n<b>👑 ADMIN COMMANDS:</b>\n🎁 <code>/add #Name 30d</code> - Give Premium\n✂️ <code>/rem_prem #Name</code> - Remove Premium\n🔇 <code>/mute [days] [reason]</code> - Mute User (Reply)\n🔊 <code>/unmute</code> - Unmute User (Reply)\n🔨 <code>/ban [days] [reason]</code> - Ban User (Reply)\n🕊️ <code>/unban</code> - Unban User (Reply)\n🔒 <code>/restrict on/off</code> - Media Protect\n🗑️ <code>/binch [id]</code> - Set Bin Channel\n⏱️ <code>/pmdlt on [secs]</code> - Auto-Delete PM\n⚙️ <code>/ref on/off</code> - Setup Referral\n📈 <code>/stats</code> - Bot Stats\n🚦 <code>/wait on/off</code> - Lock Registration\n📢 <code>/broadcast</code> - Mass Message (Reply)\n💬 <code>/chat on/off</code> - Toggle Global Chat"
    await message.reply(txt)
@Client.on_message(filters.command("mute") & filters.user(Config.ADMIN_IDS))
async def mute_cmd(client, message):
    try:
        if not message.reply_to_message or not (message.reply_to_message.caption or message.reply_to_message.text): return await message.reply("❌ <b>Error:</b> Reply to a user's forwarded media/chat to mute.")
        content = message.reply_to_message.caption or message.reply_to_message.text
        match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
        if not match: return await message.reply("❌ <b>Error:</b> Could not extract Anonymous Nickname.")
        nick = match.group(1).strip()
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply("❌ <b>Error:</b> User not found.")
        args = message.command[1:]
        days, reason = 1, "Violating Rules"
        if len(args) > 0 and args[0].isdigit(): days = int(args[0]); reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0: reason = " ".join(args)
        await db.mute_user(u['user_id'], days * 24)
        await message.reply(f"🔇 <b>Muted:</b> #{nick}\n⏳ <b>Duration:</b> {days} Days\n📝 <b>Reason:</b> {reason}")
        try: await client.send_message(u['user_id'], f"🔇 <b>You have been MUTED for {days} days.</b>\n📝 <b>Reason:</b> {reason}\n<i>You cannot send or receive media.</i>")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("unmute") & filters.user(Config.ADMIN_IDS))
async def unmute_cmd(client, message):
    try:
        if not message.reply_to_message: return await message.reply("❌ <b>Error:</b> Reply to user's message to unmute.")
        content = message.reply_to_message.caption or message.reply_to_message.text
        match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
        if not match: return await message.reply("❌ <b>Error:</b> Could not extract Nickname.")
        u = await db.get_user_by_nickname(match.group(1).strip())
        if not u: return await message.reply("❌ <b>Error:</b> User not found.")
        await db.unmute_user(u['user_id'])
        await message.reply(f"🔊 <b>Unmuted:</b> #{u['nickname']}")
        try: await client.send_message(u['user_id'], "🔊 <b>You have been UNMUTED. Welcome back!</b>")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("ban") & filters.user(Config.ADMIN_IDS))
async def ban_cmd(client, message):
    try:
        if not message.reply_to_message or not (message.reply_to_message.caption or message.reply_to_message.text): return await message.reply("❌ <b>Error:</b> Reply to a user's message to ban.")
        content = message.reply_to_message.caption or message.reply_to_message.text
        match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
        if not match: return await message.reply("❌ <b>Error:</b> Could not extract Nickname.")
        nick = match.group(1).strip()
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply("❌ <b>Error:</b> User not found.")
        args = message.command[1:]
        days, reason = 365, "Severe Violation"
        if len(args) > 0 and args[0].isdigit(): days = int(args[0]); reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0: reason = " ".join(args)
        await db.ban_user(u['user_id'], days)
        await message.reply(f"🔨 <b>Banned:</b> #{nick}\n⏳ <b>Duration:</b> {days} Days\n📝 <b>Reason:</b> {reason}")
        try: await client.send_message(u['user_id'], f"🚨 <b>You have been BANNED for {days} days.</b>\n📝 <b>Reason:</b> {reason}")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("unban") & filters.user(Config.ADMIN_IDS))
async def unban_cmd(client, message):
    try:
        if not message.reply_to_message: return await message.reply("❌ <b>Error:</b> Reply to user's message to unban.")
        content = message.reply_to_message.caption or message.reply_to_message.text
        match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
        if not match: return await message.reply("❌ <b>Error:</b> Could not extract Nickname.")
        u = await db.get_user_by_nickname(match.group(1).strip())
        if not u: return await message.reply("❌ <b>Error:</b> User not found.")
        await db.unban_user(u['user_id'])
        await message.reply(f"🕊️ <b>Unbanned:</b> #{u['nickname']}")
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("chat") & filters.user(Config.ADMIN_IDS))
async def toggle_chat(client, message):
    try:
        if len(message.command) < 2: return await message.reply("💬 <b>Usage:</b> `/chat on` or `/chat off`")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"chat_enabled": mode})
        await message.reply(f"💬 Global Chat: <b>{'ON' if mode else 'OFF'}</b>")
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("stats") & filters.user(Config.ADMIN_IDS))
async def stats_cmd(client, message):
    try:
        t, a, b = await db.get_stats()
        await message.reply(f"📊 <b>Bot Stats:</b>\n👥 Total Users: {t}\n🟢 Active: {a}\n🔴 Banned: {b}\n⏱ Uptime: {get_uptime()}")
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("add") & filters.user(Config.ADMIN_IDS))
async def manual_add(client, message):
    try:
        if len(message.command) < 3: return await message.reply("🎁 <b>Usage:</b> `/add #Nickname 30d`")
        nick = message.command[1].replace("#", "")
        dur = parse_duration(message.command[2])
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply(f"❌ <b>Error:</b> User #{nick} not found.")
        if dur:
            await users.update_one({"user_id": u['user_id']}, {"$set": {"is_premium": True, "premium_expiry": datetime.now() + dur}})
            await message.reply(f"✅ <b>Premium Added:</b> #{nick} for {message.command[2]}")
            try: await client.send_message(u['user_id'], "💎 <b>Premium Access Granted!</b> Enjoy unlimited zero-delay media.")
            except: pass
        else: await message.reply("❌ <b>Error:</b> Invalid duration format (use 1d, 30m, 1h).")
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("rem_prem") & filters.user(Config.ADMIN_IDS))
async def rem_prem_cmd(client, message):
    try:
        if len(message.command) < 2: return await message.reply("✂️ <b>Usage:</b> `/rem_prem #Nickname`")
        nick = message.command[1].replace("#", "")
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply(f"❌ <b>Error:</b> User #{nick} not found.")
        await db.remove_premium(u['user_id'])
        await message.reply(f"✅ <b>Premium Removed:</b> #{nick}")
        try: await client.send_message(u['user_id'], "⚠️ <b>PREMIUM ACCESS REMOVED BY ADMIN.</b>")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("restrict") & filters.user(Config.ADMIN_IDS))
async def restrict_cmd(client, message):
    try:
        if len(message.command) < 2: return await message.reply("🔒 <b>Usage:</b> `/restrict on` or `/restrict off`")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"media_restriction": mode})
        await message.reply(f"✅ <b>Media Restriction:</b> {'ON' if mode else 'OFF'}")
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("binch") & filters.user(Config.ADMIN_IDS))
async def set_bin(client, message):
    try:
        if len(message.command) < 2: return await message.reply("🗑️ <b>Usage:</b> `/binch -100xxxxxxxx`")
        cid = int(message.command[1]) if message.command[1].lstrip('-').isdigit() else message.command[1]
        await db.update_settings({"bin_channel": cid})
        await message.reply(f"✅ <b>Bin Channel Set:</b> {cid}")
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("wait") & filters.user(Config.ADMIN_IDS))
async def wait_cmd(client, message):
    try:
        if len(message.command) < 2: return await message.reply("🚦 <b>Usage:</b> `/wait on` (Lock) or `/wait off` (Open)")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"registration_open": not mode})
        await message.reply(f"✅ <b>Registration Locked:</b> {'YES' if mode else 'NO'}")
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.command("pmdlt") & filters.user(Config.ADMIN_IDS))
async def toggle_dlt(client, message):
    try:
        if len(message.command) < 2: return await message.reply("⏱️ <b>Usage:</b> `/pmdlt on 60` or `/pmdlt off`")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"pm_dlt": mode})
        if mode and len(message.command) >= 3: await db.update_settings({"dlt_time": int(message.command[2])})
        await message.reply(f"✅ <b>Auto-Delete:</b> {'ON' if mode else 'OFF'}")
    except Exception as e: await message.reply(f"❌ <b>Error:</b> {e}")
@Client.on_message(filters.text & filters.user(Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "join", "me", "register", "referral", "chat"]))
async def admin_state_handler(client, message):
    uid = message.from_user.id
    if uid not in admin_states: return
    state = admin_states[uid]
    if state.get("step") == "ref_1":
        try: state["count"], state["step"] = int(message.text), "ref_2"; await message.reply("📝 <b>Send invite text.</b>")
        except: await message.reply("❌ Invalid number.")
    elif state.get("step") == "ref_2":
        state["text"], state["step"] = message.text.html, "ref_3"
        await message.reply("⏱ <b>Send duration (e.g. 7d).</b>")
    elif state.get("step") == "ref_3":
        if parse_duration(message.text):
            await db.update_settings({"ref_system": True, "ref_count": state["count"], "ref_text": state["text"], "ref_time_str": message.text})
            admin_states.pop(uid, None)
            await message.reply("✅ <b>Referral Setup Done.</b>")
        else: await message.reply("❌ Invalid format. Use 7d, 1M, etc.")
