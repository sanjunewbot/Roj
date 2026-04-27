import random
import re
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions

import config
from database import db, users
from utils import check_fsub, parse_duration, build_start_text, start_keyboard, history_reply_keyboard, get_uptime, get_time_left

ADJECTIVES = ["Foggy", "Silent", "Hidden", "Dark", "Ghost", "Mystic", "Shadow", "Secret", "Neon", "Cyber"]
NOUNS = ["Wolf", "Raven", "Sniper", "Hunter", "Storm", "Ninja", "Phantom", "Dragon", "Specter", "Viper"]

@Client.on_chat_join_request()
async def handle_join_request(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    user = await db.get_user(user_id)
    if not user:
        random_name = f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1000, 9999)}"
        await db.add_user(user_id, random_name)
        
    await db.add_requested_channel(user_id, chat_id)
    try: 
        await client.send_message(user_id, "✅ <b>Join request registered!</b> You now have access. Please type /start to continue.")
    except: 
        pass

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    bot_config = await db.get_bot_settings()
    user = await db.get_user(user_id)
    
    if not user and not bot_config.get('registration_open', True):
        return await message.reply("🚫 <b>Registration Locked by Administrators.</b>")

    if len(message.command) > 1 and message.command[1].startswith("ref_"):
        try:
            inviter_id = int(message.command[1].split("_")[1])
            if inviter_id != user_id and not user and bot_config.get('ref_system'):
                await users.update_one({"user_id": inviter_id}, {"$inc": {"ref_balance": 1}})
                inviter = await db.get_user(inviter_id)
                try: await client.send_message(inviter_id, f"🎉 <b>New Referral!</b> Points: {inviter['ref_balance']}/{bot_config['ref_count']}")
                except: pass
                if inviter['ref_balance'] >= bot_config['ref_count']:
                    duration = parse_duration(bot_config['ref_time_str'])
                    if duration:
                        expiry = datetime.now() + duration
                        await users.update_one({"user_id": inviter_id}, {"$set": {"is_premium": True, "premium_expiry": expiry}, "$inc": {"ref_balance": -bot_config['ref_count']}})
                        try: await client.send_message(inviter_id, "🎊 <b>VIP Premium Activated!</b>")
                        except: pass
        except: pass

    if not user:
        random_name = f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1000, 9999)}"
        await db.add_user(user_id, random_name)
        user = await db.get_user(user_id)

    is_joined, result = await check_fsub(client, user_id)
    if not is_joined:
        if result == "not_admin":
            return await message.reply("⚠️ <b>System Error:</b> Bot is not an admin in the mandatory channel(s). Please contact support.")
        buttons = []
        for item in result:
            buttons.append([InlineKeyboardButton(item["text"], url=item["url"])])
        return await message.reply("❌ <b>Access Denied!</b>\nYou must join or send join requests to all mandatory networks below.\n\n<i>Note: Once you request, come back and type /start</i>", reply_markup=InlineKeyboardMarkup(buttons))

    time_val = "Unlimited" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    status_val = "VIP" if user.get('is_premium') else "Free"
    welcome_msg = config.START_TEXT_TEMPLATE.format(name=user['nickname'], time=time_val, status=status_val)
    
    t_link = bot_config.get("tutorial_link")
    
    await message.reply(
        welcome_msg, 
        reply_markup=start_keyboard(bot_config.get('ref_system'), t_link), 
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    
    menu_msg = "💡 <b>System UI Loaded.</b>"
    await message.reply(menu_msg, reply_markup=history_reply_keyboard(bot_config.get('get_btn_enabled')))

@Client.on_message(filters.command("register") & filters.private)
async def register_cmd(client, message):
    is_joined, _ = await check_fsub(client, message.from_user.id)
    if not is_joined: return
    if len(message.command) < 2: return await message.reply("📝 <b>Format:</b> `/register [NewName]`")
    await users.update_one({"user_id": message.from_user.id}, {"$set": {"nickname": message.command[1]}})
    await message.reply(f"✅ Your anonymous identity has been updated to '<b>{message.command[1]}</b>'.")

@Client.on_message(filters.command("me") & filters.private)
async def me_cmd(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user: return

    status = "VIP Premium" if user.get('is_premium') else "Standard Free"
    time_left = "Unlimited" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    
    expiry_info = ""
    if user.get('premium_expiry'):
        expiry_info = f"📅 <b>Expiry Date:</b> <code>{user['premium_expiry'].strftime('%Y-%m-%d %H:%M')}</code>\n"

    me_msg = config.ME_TEXT_TEMPLATE.format(
        name=user['nickname'],
        user_id=user_id,
        status=status,
        total_sent=user.get('total_sent', 0),
        ref_bal=user.get('ref_balance', 0),
        time_left=time_left,
        expiry_info=expiry_info
    )
    await message.reply(me_msg)

@Client.on_message(filters.command("join") & filters.private)
async def join_cmd(client, message):
    await message.reply(config.JOIN_TEXT)

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    txt = (
        "🛠 <b>BOT COMMAND DIRECTORY</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👤 <b>USER COMMANDS:</b>\n"
        "• /start - Dashboard & Status\n"
        "• /me - Detailed Profile Stats\n"
        "• /register [name] - Change Identity\n"
        "• /referral - Earn VIP access\n"
        "• /join - Plan Benefits\n"
        "• /help - This Menu\n"
    )
    if message.from_user.id in config.Config.ADMIN_IDS:
        txt += (
            "\n👑 <b>ADMIN COMMANDS:</b>\n"
            "• /stats - Live System Diagnostics\n"
            "• /add #Name 30d - Give Premium\n"
            "• /rem_prem #Name - Remove Premium\n"
            "• /mute [#Name] [days] [reason] - Mute User\n"
            "• /unmute [#Name] - Unmute User\n"
            "• /ban [#Name] [days] [reason] - Ban User\n"
            "• /unban [#Name] - Unban User\n"
            "• /broadcast - Global Message (Reply)\n"
            "• /chat on/off - Toggle Global Chat\n"
            "• /restrict on/off - Protection Mode\n"
            "• /binch [id] - Set Backup Bin\n"
            "• /wait on/off - Registration Lock\n"
            "• /pmdlt on [secs] - Auto Purge Setup\n"
            "• /ref on/off - Referral Config\n"
            "• /get_buttn on/off - Toggle Media History\n"
            "• /tutorial on/off - Manage Video Tutorial"
        )
    await message.reply(txt)

@Client.on_message(filters.command("mute") & filters.user(config.Config.ADMIN_IDS))
async def mute_cmd(client, message):
    try:
        nick = None
        args = []
        if len(message.command) > 1 and message.command[1].startswith("#"):
            nick = message.command[1].replace("#", "")
            args = message.command[2:]
        elif message.reply_to_message and (message.reply_to_message.caption or message.reply_to_message.text):
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match: nick = match.group(1).strip()
            args = message.command[1:]
            
        if not nick: return await message.reply("❌ <b>Error:</b> Reply to a message or use `/mute #Nickname`.")
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply(f"❌ <b>Error:</b> Identity #{nick} not found.")
        if u['user_id'] in config.Config.ADMIN_IDS: return await message.reply("❌ <b>Action Denied:</b> Administrators possess system immunity.")
            
        days, reason = 1, "Violation of Network Guidelines"
        if len(args) > 0 and args[0].isdigit():
            days = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0:
            reason = " ".join(args)
            
        await db.mute_user(u['user_id'], days * 24)
        await message.reply(f"🔇 <b>Target Silenced:</b> #{nick}\n⏳ <b>Duration:</b> {days} Days\n📝 <b>Reason:</b> {reason}")
        
        try: await client.send_message(u['user_id'], f"🔇 <b>System Alert: You have been MUTED for {days} days.</b>\n📝 <b>Reason:</b> {reason}\n<i>Transmitting and receiving media is disabled.</i>")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("unmute") & filters.user(config.Config.ADMIN_IDS))
async def unmute_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"):
            nick = message.command[1].replace("#", "")
        elif message.reply_to_message:
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match: nick = match.group(1).strip()
                
        if not nick: return await message.reply("❌ <b>Error:</b> Reply to a message or use `/unmute #Nickname`.")
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply("❌ <b>Error:</b> User record not found.")
            
        await db.unmute_user(u['user_id'])
        await message.reply(f"🔊 <b>Silence Revoked:</b> #{u['nickname']}")
        try: await client.send_message(u['user_id'], "🔊 <b>Your account restrictions have been lifted. Welcome back.</b>")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("ban") & filters.user(config.Config.ADMIN_IDS))
async def ban_cmd(client, message):
    try:
        nick = None
        args = []
        if len(message.command) > 1 and message.command[1].startswith("#"):
            nick = message.command[1].replace("#", "")
            args = message.command[2:]
        elif message.reply_to_message and (message.reply_to_message.caption or message.reply_to_message.text):
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match: nick = match.group(1).strip()
            args = message.command[1:]
            
        if not nick: return await message.reply("❌ <b>Error:</b> Reply to a message or use `/ban #Nickname`.")
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply(f"❌ <b>Error:</b> Identity #{nick} not found.")
        if u['user_id'] in config.Config.ADMIN_IDS: return await message.reply("❌ <b>Action Denied:</b> Administrators possess system immunity.")
            
        days, reason = 365, "Severe Protocol Violation"
        if len(args) > 0 and args[0].isdigit():
            days = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0:
            reason = " ".join(args)
            
        await db.ban_user(u['user_id'], days)
        await message.reply(f"🔨 <b>Target Banished:</b> #{nick}\n⏳ <b>Duration:</b> {days} Days\n📝 <b>Reason:</b> {reason}")
        try: await client.send_message(u['user_id'], f"🚨 <b>CRITICAL ALERT: Your network access has been permanently revoked for {days} days.</b>\n📝 <b>Reason:</b> {reason}")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("unban") & filters.user(config.Config.ADMIN_IDS))
async def unban_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"):
            nick = message.command[1].replace("#", "")
        elif message.reply_to_message:
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match: nick = match.group(1).strip()
                
        if not nick: return await message.reply("❌ <b>Error:</b> Reply to a message or use `/unban #Nickname`.")
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply("❌ <b>Error:</b> User record not found.")
            
        await db.unban_user(u['user_id'])
        await message.reply(f"🕊️ <b>Target Pardoned:</b> #{u['nickname']}")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("chat") & filters.user(config.Config.ADMIN_IDS))
async def toggle_chat(client, message):
    try:
        if len(message.command) < 2: return await message.reply("💬 <b>Syntax:</b> `/chat on` or `/chat off`")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"chat_enabled": mode})
        await message.reply(f"💬 Global Chat Protocol is now: <b>{'ONLINE' if mode else 'OFFLINE'}</b>")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("stats") & filters.user(config.Config.ADMIN_IDS))
async def stats_cmd(client, message):
    try:
        t, a, b = await db.get_stats()
        await message.reply(
            f"📈 <b>SYSTEM DIAGNOSTICS</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Total Identities:</b> <code>{t}</code>\n"
            f"🟢 <b>Active Nodes:</b> <code>{a}</code>\n"
            f"🔴 <b>Banished Entities:</b> <code>{b}</code>\n"
            f"⏱ <b>Core Uptime:</b> <code>{get_uptime()}</code>\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("add") & filters.user(config.Config.ADMIN_IDS))
async def manual_add(client, message):
    try:
        if len(message.command) < 3: return await message.reply("🎁 <b>Syntax:</b> `/add #Nickname 30d`")
        nick = message.command[1].replace("#", "")
        dur = parse_duration(message.command[2])
        u = await db.get_user_by_nickname(nick)
        
        if not u: return await message.reply(f"❌ <b>Error:</b> Identity #{nick} does not exist.")
        if dur:
            await users.update_one({"user_id": u['user_id']}, {"$set": {"is_premium": True, "premium_expiry": datetime.now() + dur}})
            await message.reply(f"✅ <b>VIP Credentials Granted:</b> #{nick} for {message.command[2]}")
            try: await client.send_message(u['user_id'], "💎 <b>VIP Premium Status Acquired!</b> You now have unlimited, zero-delay access.")
            except: pass
        else: await message.reply("❌ <b>Error:</b> Invalid time parameter (acceptable: 1d, 30m, 1h).")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("rem_prem") & filters.user(config.Config.ADMIN_IDS))
async def rem_prem_cmd(client, message):
    try:
        if len(message.command) < 2: return await message.reply("✂️ <b>Syntax:</b> `/rem_prem #Nickname`")
        nick = message.command[1].replace("#", "")
        u = await db.get_user_by_nickname(nick)
        if not u: return await message.reply(f"❌ <b>Error:</b> Identity #{nick} does not exist.")
            
        await db.remove_premium(u['user_id'])
        await message.reply(f"✅ <b>VIP Credentials Revoked:</b> #{nick}")
        try: await client.send_message(u['user_id'], "⚠️ <b>WARNING: YOUR VIP ACCESS HAS BEEN TERMINATED BY COMMAND CENTER.</b>")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("restrict") & filters.user(config.Config.ADMIN_IDS))
async def restrict_cmd(client, message):
    try:
        if len(message.command) < 2: return await message.reply("🔒 <b>Syntax:</b> `/restrict on` or `/restrict off`")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"media_restriction": mode})
        await message.reply(f"✅ <b>Media Forwarding Protection:</b> {'ENGAGED' if mode else 'DISENGAGED'}")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("binch") & filters.user(config.Config.ADMIN_IDS))
async def set_bin(client, message):
    try:
        if len(message.command) < 2: return await message.reply("🗑️ <b>Syntax:</b> `/binch -100xxxxxxxx`")
        cid = int(message.command[1]) if message.command[1].lstrip('-').isdigit() else message.command[1]
        await db.update_settings({"bin_channel": cid})
        await message.reply(f"✅ <b>Backup Archive Re-routed to:</b> {cid}")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("wait") & filters.user(config.Config.ADMIN_IDS))
async def wait_cmd(client, message):
    try:
        if len(message.command) < 2: return await message.reply("🚦 <b>Syntax:</b> `/wait on` (Lock) or `/wait off` (Open)")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"registration_open": not mode})
        await message.reply(f"✅ <b>Network Entry Lock:</b> {'ACTIVE' if mode else 'DISABLED'}")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("pmdlt") & filters.user(config.Config.ADMIN_IDS))
async def toggle_dlt(client, message):
    try:
        if len(message.command) < 2: return await message.reply("⏱️ <b>Syntax:</b> `/pmdlt on 60` or `/pmdlt off`")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"pm_dlt": mode})
        if mode and len(message.command) >= 3:
            await db.update_settings({"dlt_time": int(message.command[2])})
        await message.reply(f"✅ <b>Auto-Purge Protocol:</b> {'ONLINE' if mode else 'OFFLINE'}")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("get_buttn") & filters.user(config.Config.ADMIN_IDS))
async def toggle_get_buttn(client, message):
    try:
        if len(message.command) < 2: return await message.reply("🎥 <b>Syntax:</b> `/get_buttn on` or `/get_buttn off`")
        mode = message.command[1].lower() == "on"
        await db.update_settings({"get_btn_enabled": mode})
        await message.reply(f"✅ <b>Media History Button:</b> {'ONLINE' if mode else 'OFFLINE'}")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("tutorial") & filters.user(config.Config.ADMIN_IDS))
async def manage_tutorial(client, message):
    try:
        if len(message.command) < 2: return await message.reply("🎬 <b>Syntax:</b> `/tutorial on` or `/tutorial off`")
        mode = message.command[1].lower()
        if mode == "off":
            await db.update_settings({"tutorial_link": None})
            await message.reply("✅ <b>Tutorial Video Disabled.</b> Crystal button hidden.")
        elif mode == "on":
            config.admin_states[message.from_user.id] = {"step": "tut_1"}
            await message.reply("🔗 <b>System Waiting:</b> Please send the Tutorial Video Link (URL).")
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

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

@Client.on_message(filters.text & filters.user(config.Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "join", "me", "register", "referral", "chat", "get_buttn", "tutorial"]) & ~filters.regex("^(GET MEDIA HISTORY)$"))
async def admin_state_handler(client, message):
    uid = message.from_user.id
    if uid not in config.admin_states: return
    state = config.admin_states[uid]
    
    if state.get("step") == "tut_1":
        link = message.text
        await db.update_settings({"tutorial_link": link})
        config.admin_states.pop(uid, None)
        await message.reply(f"✅ <b>System Tutorial Link Updated & Activated:</b>\n{link}")
        
    elif state.get("step") == "ref_1":
        try:
            state["count"] = int(message.text)
            state["step"] = "ref_2"
            await message.reply("📝 <b>Step 2:</b> Provide the custom invitation text (HTML supported).")
        except ValueError:
            await message.reply("❌ <b>Invalid Input:</b> Please provide a numeric value.")
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
