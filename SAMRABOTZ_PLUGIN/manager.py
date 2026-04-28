import re
from datetime import datetime
from pyrogram import Client, filters
import config
from database import db, users
from utils import get_uptime, parse_duration

@Client.on_message(filters.command("stats") & filters.user(config.Config.ADMIN_IDS))
async def stats_cmd(client, message):
    try:
        t, a, b = await db.get_stats()
        await message.reply(f"📈 <b>SYSTEM DIAGNOSTICS</b>\n━━━━━━━━━━━━━━━━━━\n👥 <b>Total Identities:</b> <code>{t}</code>\n🟢 <b>Active Nodes:</b> <code>{a}</code>\n🔴 <b>Banished Entities:</b> <code>{b}</code>\n⏱ <b>Core Uptime:</b> <code>{get_uptime()}</code>\n━━━━━━━━━━━━━━━━━━")
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
        elif len(args) > 0: reason = " ".join(args)
        await db.mute_user(u['user_id'], days * 24)
        await message.reply(f"🔇 <b>Target Silenced:</b> #{nick}\n⏳ <b>Duration:</b> {days} Days\n📝 <b>Reason:</b> {reason}")
        try: await client.send_message(u['user_id'], f"🔇 <b>System Alert: You have been MUTED for {days} days.</b>\n📝 <b>Reason:</b> {reason}\n<i>Transmitting and receiving media is disabled.</i>")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("unmute") & filters.user(config.Config.ADMIN_IDS))
async def unmute_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"): nick = message.command[1].replace("#", "")
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
        elif len(args) > 0: reason = " ".join(args)
        await db.ban_user(u['user_id'], days)
        await message.reply(f"🔨 <b>Target Banished:</b> #{nick}\n⏳ <b>Duration:</b> {days} Days\n📝 <b>Reason:</b> {reason}")
        try: await client.send_message(u['user_id'], f"🚨 <b>CRITICAL ALERT: Your network access has been permanently revoked for {days} days.</b>\n📝 <b>Reason:</b> {reason}")
        except: pass
    except Exception as e: await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("unban") & filters.user(config.Config.ADMIN_IDS))
async def unban_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"): nick = message.command[1].replace("#", "")
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
        if mode and len(message.command) >= 3: await db.update_settings({"dlt_time": int(message.command[2])})
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

@Client.on_message(filters.text & filters.private & filters.user(config.Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "plans", "me", "register", "referral", "chat", "get_buttn", "tutorial"]) & ~filters.regex("^(GET MEDIA HISTORY)$"))
async def master_admin_state_handler(client, message):
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
