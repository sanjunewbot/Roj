import re
import logging
from datetime import datetime
from pyrogram import Client, filters
import config
from database import db, users
from utils import get_uptime, parse_duration

logger = logging.getLogger("MANAGER")

@Client.on_message(filters.command("stats") & filters.user(config.Config.ADMIN_IDS))
async def stats_cmd(client, message):
    try:
        t, a, b = await db.get_stats()
        await message.reply(f"> 📈 <b>System diagnostics</b>\n> \n> 👥 <b>Total identities:</b> <code>{t}</code>\n> 🟢 <b>Active nodes:</b> <code>{a}</code>\n> 🔴 <b>Banished entities:</b> <code>{b}</code>\n> ⏱ <b>Core uptime:</b> <code>{get_uptime()}</code>")
    except Exception as e: 
        logger.error(f"Stats command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("add") & filters.user(config.Config.ADMIN_IDS))
async def manual_add(client, message):
    try:
        if len(message.command) < 3: 
            return await message.reply("> 🎁 <b>Syntax error</b>\n> \n> Use format: <code>/add #Nickname 30d</code>")
            
        nick = message.command[1].replace("#", "")
        dur = parse_duration(message.command[2])
        u = await db.get_user_by_nickname(nick)
        
        if not u: 
            return await message.reply(f"> ❌ <b>Error</b>\n> \n> Identity #{nick} does not exist.")
            
        if dur:
            await users.update_one({"user_id": u['user_id']}, {"$set": {"is_premium": True, "premium_expiry": datetime.now() + dur}})
            await message.reply(f"> ✅ <b>VIP credentials granted</b>\n> \n> Granted to #{nick} for {message.command[2]}.")
            try: 
                await client.send_message(u['user_id'], "> 💎 <b>VIP premium status acquired</b>\n> \n> You now have unlimited, zero-delay access.")
            except Exception as e: 
                logger.error(f"Failed to notify user {u['user_id']} of premium addition: {str(e)}", exc_info=True)
        else: 
            await message.reply("> ❌ <b>Error</b>\n> \n> Invalid time parameter. Acceptable formats: 1d, 30m, 1h.")
    except Exception as e: 
        logger.error(f"Add premium command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("rem_prem") & filters.user(config.Config.ADMIN_IDS))
async def rem_prem_cmd(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> ✂️ <b>Syntax error</b>\n> \n> Use format: <code>/rem_prem #Nickname</code>")
            
        nick = message.command[1].replace("#", "")
        u = await db.get_user_by_nickname(nick)
        
        if not u: 
            return await message.reply(f"> ❌ <b>Error</b>\n> \n> Identity #{nick} does not exist.")
            
        await db.remove_premium(u['user_id'])
        await message.reply(f"> ✅ <b>VIP credentials revoked</b>\n> \n> Target: #{nick}")
        try: 
            await client.send_message(u['user_id'], "> ⚠️ <b>Warning</b>\n> \n> Your VIP access has been terminated by command center.")
        except Exception as e: 
            logger.error(f"Failed to notify user {u['user_id']} of premium removal: {str(e)}", exc_info=True)
    except Exception as e: 
        logger.error(f"Remove premium command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

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
            match = re.search(r"#([a-zA-Z0-9_]+)", content)
            if match: nick = match.group(1).strip()
            args = message.command[1:]
            
        if not nick: 
            return await message.reply("> ❌ <b>Error</b>\n> \n> Reply to a message or use <code>/mute #Nickname</code>.")
            
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await message.reply(f"> ❌ <b>Error</b>\n> \n> Identity #{nick} not found.")
            
        if u['user_id'] in config.Config.ADMIN_IDS: 
            return await message.reply("> ❌ <b>Action denied</b>\n> \n> Administrators possess system immunity.")
            
        days, reason = 1, "Violation of network guidelines"
        if len(args) > 0 and args[0].isdigit():
            days = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0: 
            reason = " ".join(args)
            
        await db.mute_user(u['user_id'], days * 24)
        await message.reply(f"> 🔇 <b>Target silenced</b>\n> \n> <b>Target:</b> #{nick}\n> <b>Duration:</b> {days} Days\n> <b>Reason:</b> {reason}")
        try: 
            await client.send_message(u['user_id'], f"> 🔇 <b>System alert</b>\n> \n> You have been MUTED for {days} days.\n> <b>Reason:</b> {reason}\n> \n> <i>Transmitting and receiving media is disabled.</i>")
        except Exception as e: 
            logger.error(f"Failed to notify user {u['user_id']} of mute: {str(e)}", exc_info=True)
    except Exception as e: 
        logger.error(f"Mute command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("unmute") & filters.user(config.Config.ADMIN_IDS))
async def unmute_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"): 
            nick = message.command[1].replace("#", "")
        elif message.reply_to_message:
            content = message.reply_to_message.caption or message.reply_to_message.text
            if content:
                match = re.search(r"#([a-zA-Z0-9_]+)", content)
                if match: nick = match.group(1).strip()
            
        if not nick: 
            return await message.reply("> ❌ <b>Error</b>\n> \n> Reply to a message or use <code>/unmute #Nickname</code>.")
            
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await message.reply("> ❌ <b>Error</b>\n> \n> User record not found.")
            
        await db.unmute_user(u['user_id'])
        await message.reply(f"> 🔊 <b>Silence revoked</b>\n> \n> Target: #{u['nickname']}")
        try: 
            await client.send_message(u['user_id'], "> 🔊 <b>Account restored</b>\n> \n> Your account restrictions have been lifted. Welcome back.")
        except Exception as e: 
            logger.error(f"Failed to notify user {u['user_id']} of unmute: {str(e)}", exc_info=True)
    except Exception as e: 
        logger.error(f"Unmute command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

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
            match = re.search(r"#([a-zA-Z0-9_]+)", content)
            if match: nick = match.group(1).strip()
            args = message.command[1:]
            
        if not nick: 
            return await message.reply("> ❌ <b>Error</b>\n> \n> Reply to a message or use <code>/ban #Nickname</code>.")
            
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await message.reply(f"> ❌ <b>Error</b>\n> \n> Identity #{nick} not found.")
            
        if u['user_id'] in config.Config.ADMIN_IDS: 
            return await message.reply("> ❌ <b>Action denied</b>\n> \n> Administrators possess system immunity.")
            
        days, reason = 365, "Severe protocol violation"
        if len(args) > 0 and args[0].isdigit():
            days = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0: 
            reason = " ".join(args)
            
        await db.ban_user(u['user_id'], days)
        await message.reply(f"> 🔨 <b>Target banished</b>\n> \n> <b>Target:</b> #{nick}\n> <b>Duration:</b> {days} Days\n> <b>Reason:</b> {reason}")
        try: 
            await client.send_message(u['user_id'], f"> 🚨 <b>Critical alert</b>\n> \n> Your network access has been permanently revoked for {days} days.\n> <b>Reason:</b> {reason}")
        except Exception as e: 
            logger.error(f"Failed to notify user {u['user_id']} of ban: {str(e)}", exc_info=True)
    except Exception as e: 
        logger.error(f"Ban command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("unban") & filters.user(config.Config.ADMIN_IDS))
async def unban_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"): 
            nick = message.command[1].replace("#", "")
        elif message.reply_to_message:
            content = message.reply_to_message.caption or message.reply_to_message.text
            if content:
                match = re.search(r"#([a-zA-Z0-9_]+)", content)
                if match: nick = match.group(1).strip()
            
        if not nick: 
            return await message.reply("> ❌ <b>Error</b>\n> \n> Reply to a message or use <code>/unban #Nickname</code>.")
            
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await message.reply("> ❌ <b>Error</b>\n> \n> User record not found.")
            
        await db.unban_user(u['user_id'])
        await message.reply(f"> 🕊️ <b>Target pardoned</b>\n> \n> Target: #{u['nickname']}")
    except Exception as e: 
        logger.error(f"Unban command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("chat") & filters.user(config.Config.ADMIN_IDS))
async def toggle_chat(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> 💬 <b>Syntax error</b>\n> \n> Use format: <code>/chat on</code> or <code>/chat off</code>")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"chat_enabled": mode})
        status = 'Online' if mode else 'Offline'
        await message.reply(f"> 💬 <b>Global chat protocol</b>\n> \n> Chat system is now: <b>{status}</b>")
    except Exception as e: 
        logger.error(f"Toggle chat command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("restrict") & filters.user(config.Config.ADMIN_IDS))
async def restrict_cmd(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> 🔒 <b>Syntax error</b>\n> \n> Use format: <code>/restrict on</code> or <code>/restrict off</code>")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"media_restriction": mode})
        status = 'Engaged' if mode else 'Disengaged'
        await message.reply(f"> ✅ <b>Media forwarding protection</b>\n> \n> Status: <b>{status}</b>")
    except Exception as e: 
        logger.error(f"Restrict command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("binch") & filters.user(config.Config.ADMIN_IDS))
async def set_bin(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> 🗑️ <b>Syntax error</b>\n> \n> Use format: <code>/binch -100xxxxxxxx</code>")
            
        cid = int(message.command[1]) if message.command[1].lstrip('-').isdigit() else message.command[1]
        await db.update_settings({"bin_channel": cid})
        await message.reply(f"> ✅ <b>Backup archive re-routed</b>\n> \n> New routing ID: {cid}")
    except Exception as e: 
        logger.error(f"Bin set command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("wait") & filters.user(config.Config.ADMIN_IDS))
async def wait_cmd(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> 🚦 <b>Syntax error</b>\n> \n> Use format: <code>/wait on</code> (Lock) or <code>/wait off</code> (Open)")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"registration_open": not mode})
        status = 'Active' if mode else 'Disabled'
        await message.reply(f"> ✅ <b>Network entry lock</b>\n> \n> Status: <b>{status}</b>")
    except Exception as e: 
        logger.error(f"Wait command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("pmdlt") & filters.user(config.Config.ADMIN_IDS))
async def toggle_dlt(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> ⏱️ <b>Syntax error</b>\n> \n> Use format: <code>/pmdlt on 60</code> or <code>/pmdlt off</code>")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"pm_dlt": mode})
        if mode and len(message.command) >= 3: 
            await db.update_settings({"dlt_time": int(message.command[2])})
            
        status = 'Online' if mode else 'Offline'
        await message.reply(f"> ✅ <b>Auto-purge protocol</b>\n> \n> Status: <b>{status}</b>")
    except Exception as e: 
        logger.error(f"Auto delete command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("get_buttn") & filters.user(config.Config.ADMIN_IDS))
async def toggle_get_buttn(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> 🎥 <b>Syntax error</b>\n> \n> Use format: <code>/get_buttn on</code> or <code>/get_buttn off</code>")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"get_btn_enabled": mode})
        status = 'Online' if mode else 'Offline'
        await message.reply(f"> ✅ <b>Media history button</b>\n> \n> Status: <b>{status}</b>")
    except Exception as e: 
        logger.error(f"Get button toggle command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.command("tutorial") & filters.user(config.Config.ADMIN_IDS))
async def manage_tutorial(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply("> 🎬 <b>Syntax error</b>\n> \n> Use format: <code>/tutorial on</code> or <code>/tutorial off</code>")
            
        mode = message.command[1].lower()
        if mode == "off":
            await db.update_settings({"tutorial_link": None})
            await message.reply("> ✅ <b>Tutorial video disabled</b>\n> \n> Crystal button is now hidden.")
        elif mode == "on":
            config.admin_states[message.from_user.id] = {"step": "tut_1"}
            await message.reply("> 🔗 <b>System waiting</b>\n> \n> Please send the tutorial video link (URL).")
    except Exception as e: 
        logger.error(f"Tutorial manage command failed: {str(e)}", exc_info=True)
        await message.reply(f"> ❌ <b>System fault</b>\n> \n> An error occurred: {e}")

@Client.on_message(filters.text & filters.private & filters.user(config.Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "plans", "me", "register", "referral", "chat", "get_buttn", "tutorial"]) & ~filters.regex("^(GET MEDIA HISTORY)$"))
async def master_admin_state_handler(client, message):
    uid = message.from_user.id
    if uid not in config.admin_states: return
    state = config.admin_states[uid]
    
    try:
        if state.get("step") == "tut_1":
            link = message.text
            await db.update_settings({"tutorial_link": link})
            config.admin_states.pop(uid, None)
            await message.reply(f"> ✅ <b>System tutorial link updated</b>\n> \n> Link activated: {link}")
            
        elif state.get("step") == "ref_1":
            try:
                state["count"] = int(message.text)
                state["step"] = "ref_2"
                await message.reply("> 📝 <b>Step 2</b>\n> \n> Provide the custom invitation text (HTML supported).")
            except ValueError:
                await message.reply("> ❌ <b>Invalid input</b>\n> \n> Please provide a numeric value.")
                
        elif state.get("step") == "ref_2":
            state["text"] = message.text
            state["step"] = "ref_3"
            await message.reply("> ⏱ <b>Final step</b>\n> \n> Provide the premium duration reward (e.g., 7d, 1M, 24h).")
            
        elif state.get("step") == "ref_3":
            if parse_duration(message.text):
                await db.update_settings({"ref_system": True, "ref_count": state["count"], "ref_text": state["text"], "ref_time_str": message.text})
                config.admin_states.pop(uid, None)
                await message.reply("> ✅ <b>Referral protocol configuration complete</b>\n> \n> System is now active.")
            else: 
                await message.reply("> ❌ <b>Invalid formatting</b>\n> \n> Please utilize proper syntax (e.g., 7d, 1M).")
    except Exception as e:
        logger.error(f"Admin state handler failed for {uid}: {str(e)}", exc_info=True)
