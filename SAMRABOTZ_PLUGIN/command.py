import random
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config, RULES_TEXT, JOIN_TEXT, admin_states
from database import db, users
from utils import check_fsub, parse_duration, build_start_text, start_keyboard, get_uptime
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
ADJECTIVES = ["Foggy", "Silent", "Hidden", "Dark", "Ghost", "Mystic", "Shadow", "Secret"]
NOUNS = ["Wolf", "Raven", "Sniper", "Hunter", "Storm", "Ninja", "Phantom", "Dragon"]
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    config = await db.get_bot_settings()
    user = await db.get_user(user_id)
    
    if not user and not config.get('registration_open', True):
        return await message.reply("🚫 <b>Registration Closed!</b>\nPlease try again later.")
    
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
                        try: await client.send_message(inviter_id, "🎊 <b>Premium activated via referrals!</b>")
                        except: pass
        except: pass

    if not await check_fsub(client, user_id):
        return await message.reply("❌ <b>Access Denied!</b>\nJoin channel first.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{Config.FORCE_SUB_CHANNEL}")]]))

    if not user:
        random_name = f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1000, 9999)}"
        await db.add_user(user_id, random_name)
        user = await db.get_user(user_id)

    await message.reply(build_start_text(user), reply_markup=start_keyboard(config.get('ref_system')), disable_web_page_preview=True)
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("register") & filters.private)
async def register_cmd(client, message):
    if not await check_fsub(client, message.from_user.id): return
    if len(message.command) < 2: return await message.reply("📝 Usage: <code>/register [new_nickname]</code>")
    await users.update_one({"user_id": message.from_user.id}, {"$set": {"nickname": message.command[1]}})
    await message.reply(f"✅ Nickname changed to '<b>{message.command[1]}</b>' successfully!")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("me") & filters.private)
async def me_cmd(client, message):
    user = await db.get_user(message.from_user.id)
    config = await db.get_bot_settings()
    if not user: return await message.reply("⚠️ Please /start the bot first.")
    status = "👑 VIP Premium" if user.get('is_premium') else "🆓 Free Tier"
    rest_status = "🔒 ON" if config.get('media_restriction') else "🔓 OFF"
    text = (f"📊 <b>Your Profile</b>\n👤 <b>Name:</b> <code>{user['nickname']}</code>\n⭐ <b>Account:</b> {status}\n🛡️ <b>Restriction:</b> {rest_status}\n📈 <b>Sent:</b> {user['total_sent']}\n👥 <b>Refs:</b> {user['ref_balance']}\n")
    if user.get('premium_expiry'): text += f"📅 <b>Expiry:</b> {user['premium_expiry'].strftime('%Y-%m-%d %H:%M')}"
    await message.reply(text)

@Client.on_message(filters.command("join") & filters.private)
async def join_cmd(client, message): await message.reply(JOIN_TEXT)
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    txt = (
        "🛠 <b>Available Commands:</b>\n\n"
        "👤 <b>User Commands:</b>\n"
        "• /start - Show welcome message\n"
        "• /register [name] - Change anonymous name\n"
        "• /me - Check stats & premium status\n"
        "• /referral - Get referral link\n"
        "• /join - VIP benefits\n"
        "• /help - Show this menu\n"
    )
    if message.from_user.id in Config.ADMIN_IDS:
        txt += (
            "\n👑 <b>Admin Commands:</b>\n"
            "• /binch [ID] - Set bin channel\n"
            "• /pmdlt on [sec] | off - Auto-delete media\n"
            "• /add [ID] [time] - Manual premium\n"
            "• /rem_prem - Remove user premium\n"
            "• /restrict on | off - Toggle media lock\n"
            "• /ref on | off - Setup referral\n"
            "• /ban [ID] [days] - Ban user\n"
            "• /unban [ID] - Unban user\n"
            "• /stats - Bot statistics\n"
            "• /wait on | off - Toggle new registrations\n"
            "• /broadcast (reply) - Send mass msg"
        )
    await message.reply(txt)
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("rem_prem") & filters.user(Config.ADMIN_IDS))
async def rem_prem_cmd(client, message):
    admin_states[message.from_user.id] = {"step": "remove_premium_id"}
    await message.reply("🎁 <b>Premium Removal Flow:</b>\n\nSEND ME <b>User ID</b>.")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.text & filters.user(Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "stats", "wait", "broadcast", "join", "me", "register", "referral"]))
async def admin_state_handler(client, message):
    uid = message.from_user.id
    if uid not in admin_states: return
    state = admin_states[uid]
    if state.get("step") == "remove_premium_id":
        try:
            target_id = int(message.text)
            target_user = await db.get_user(target_id)
            if not target_user: return await message.reply("❌ User database me nahi mila.")
            await db.remove_premium(target_id)
            admin_states.pop(uid, None)
            await message.reply(f"✅ User <code>{target_id}</code> ka premium hataya gaya.")
            try: await client.send_message(target_id, "⚠️ <b>UR PREMIUM REMOVED CONTACT ADMIN</b>")
            except: pass
        except ValueError: await message.reply("❌ Invalid User ID. Sirf numbers bhejo.")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("restrict") & filters.user(Config.ADMIN_IDS))
async def restrict_cmd(client, message):
    if len(message.command) < 2: return await message.reply("🔒 Usage: /restrict on/off")
    mode = message.command[1].lower() == "on"
    await db.update_settings({"media_restriction": mode})
    await message.reply(f"✅ Media Restriction: <b>{'ON' if mode else 'OFF'}</b>")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("stats") & filters.user(Config.ADMIN_IDS))
async def stats_cmd(client, message):
    total, active, banned = await db.get_stats()
    await message.reply(f"📊 <b>Stats</b>\n👥 Total: {total}\n🟢 Active: {active}\n⛔ Banned: {banned}\n⏱ Uptime: {get_uptime()}")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("binch") & filters.user(Config.ADMIN_IDS))
async def set_bin(client, message):
    if len(message.command) < 2: return await message.reply("⚙️ Usage: /binch [ID]")
    cid = int(message.command[1]) if message.command[1].lstrip('-').isdigit() else message.command[1]
    await db.update_settings({"bin_channel": cid})
    await message.reply(f"✅ Bin set to <code>{cid}</code>")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("add") & filters.user(Config.ADMIN_IDS))
async def manual_add(client, message):
    if len(message.command) < 3: return await message.reply("⚙️ Usage: /add [ID] [time]")
    try:
        dur = parse_duration(message.command[2])
        if dur:
            await users.update_one({"user_id": int(message.command[1])}, {"$set": {"is_premium": True, "premium_expiry": datetime.now() + dur}})
            await message.reply("✅ Premium added.")
    except: pass
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("wait") & filters.user(Config.ADMIN_IDS))
async def wait_cmd(client, message):
    if len(message.command) < 2: return await message.reply("⚙️ Usage: <code>/wait on</code> or <code>/wait off</code>")
    mode = message.command[1].lower() == "on"
    await db.update_settings({"registration_open": not mode})
    await message.reply(f"✅ Wait mode is now <b>{'ON' if mode else 'OFF'}</b>.")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("pmdlt") & filters.user(Config.ADMIN_IDS))
async def toggle_dlt(client, message):
    if len(message.command) < 2: return await message.reply("⚙️ Usage: <code>/pmdlt on [sec]</code> or <code>/pmdlt off</code>")
    mode = message.command[1].lower() == "on"
    await db.update_settings({"pm_dlt": mode})
    if mode and len(message.command) >= 3:
        try: await db.update_settings({"dlt_time": int(message.command[2])})
        except: pass
    await message.reply(f"✅ Auto-Delete Engine is now <b>{'ON' if mode else 'OFF'}</b>")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("ban") & filters.user(Config.ADMIN_IDS))
async def ban_cmd(client, message):
    if len(message.command) < 3: return await message.reply("⚙️ Usage: <code>/ban [user_id] [days]</code>")
    try: await db.ban_user(int(message.command[1]), int(message.command[2]))
    except: pass
    await message.reply("✅ User banned.")
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
@Client.on_message(filters.command("unban") & filters.user(Config.ADMIN_IDS))
async def unban_cmd(client, message):
    if len(message.command) < 2: return await message.reply("⚙️ Usage: <code>/unban [user_id]</code>")
    try: await db.unban_user(int(message.command[1]))
    except: pass
    await message.reply("✅ User unbanned.")