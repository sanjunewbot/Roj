import random
import re
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Config, RULES_TEXT, JOIN_TEXT, admin_states
from database import db, users
from utils import check_fsub, parse_duration, build_start_text, start_keyboard, get_uptime

ADJECTIVES = ["Foggy", "Silent", "Hidden", "Dark", "Ghost", "Mystic", "Shadow", "Secret", "Neon", "Cyber"]
NOUNS = ["Wolf", "Raven", "Sniper", "Hunter", "Storm", "Ninja", "Phantom", "Dragon", "Specter", "Viper"]

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    config = await db.get_bot_settings()
    user = await db.get_user(user_id)
    
    if not user and not config.get('registration_open', True):
        return await message.reply("🚫 <b>Registration is currently closed by Administrators.</b>")
        
    if len(message.command) > 1 and message.command[1].startswith("ref_"):
        try:
            inviter_id = int(message.command[1].split("_")[1])
            if inviter_id != user_id and not user and config.get('ref_system'):
                await users.update_one({"user_id": inviter_id}, {"$inc": {"ref_balance": 1}})
                inviter = await db.get_user(inviter_id)
                try:
                    await client.send_message(inviter_id, f"🎉 <b>New Referral Registered!</b>\nPoints: {inviter['ref_balance']}/{config['ref_count']}")
                except:
                    pass
                if inviter['ref_balance'] >= config['ref_count']:
                    duration = parse_duration(config['ref_time_str'])
                    if duration:
                        expiry = datetime.now() + duration
                        await users.update_one(
                            {"user_id": inviter_id}, 
                            {"$set": {"is_premium": True, "premium_expiry": expiry}, "$inc": {"ref_balance": -config['ref_count']}}
                        )
                        try:
                            await client.send_message(inviter_id, "🎊 <b>Congratulations! VIP Premium has been automatically activated.</b>")
                        except:
                            pass
        except:
            pass

    is_joined, link_or_status = await check_fsub(client, user_id)
    if not is_joined:
        if link_or_status == "not_admin":
            return await message.reply("⚠️ <b>System Error:</b> The bot is currently not an admin in the mandatory joining channel. Please contact the administrator.")
        else:
            return await message.reply(
                "❌ <b>Access Denied!</b>\n\nYou must join our official network to utilize this system.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=link_or_status)]])
            )

    if not user:
        random_name = f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1000, 9999)}"
        await db.add_user(user_id, random_name)
        user = await db.get_user(user_id)
        
    await message.reply(build_start_text(user), reply_markup=start_keyboard(config.get('ref_system')), disable_web_page_preview=True)

@Client.on_message(filters.command("register") & filters.private)
async def register_cmd(client, message):
    is_joined, _ = await check_fsub(client, message.from_user.id)
    if not is_joined:
        return
        
    if len(message.command) < 2:
        return await message.reply("📝 <b>Format:</b> `/register [NewName]`")
        
    await users.update_one({"user_id": message.from_user.id}, {"$set": {"nickname": message.command[1]}})
    await message.reply(f"✅ Your anonymous identity has been updated to '<b>{message.command[1]}</b>'.")

@Client.on_message(filters.command("me") & filters.private)
async def me_cmd(client, message):
    user = await db.get_user(message.from_user.id)
    if not user:
        return
        
    status = "👑 VIP Premium Access" if user.get('is_premium') else "🆓 Standard Free Tier"
    text = (
        f"📊 <b>Profile Statistics</b>\n"
        f"👤 <b>Identity:</b> <code>{user['nickname']}</code>\n"
        f"⭐ <b>Account Level:</b> {status}\n"
        f"📈 <b>Total Media Sent:</b> {user['total_sent']}\n"
        f"👥 <b>Referral Points:</b> {user['ref_balance']}\n"
    )
    if user.get('premium_expiry'):
        text += f"📅 <b>VIP Expiry Date:</b> {user['premium_expiry'].strftime('%Y-%m-%d %H:%M')}"
        
    await message.reply(text)

@Client.on_message(filters.command("join") & filters.private)
async def join_cmd(client, message):
    await message.reply(JOIN_TEXT)

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    txt = (
        "🛠 <b>SYSTEM COMMAND DIRECTORY</b>\n\n"
        "<b>👤 STANDARD ACCESS:</b>\n"
        "🚀 <code>/start</code> - Access Dashboard\n"
        "🎭 <code>/register [name]</code> - Change Identity\n"
        "📊 <code>/me</code> - Check Account Status\n"
        "👥 <code>/referral</code> - Earn Premium Status\n"
        "💎 <code>/join</code> - View Elite Benefits\n"
    )
    if message.from_user.id in Config.ADMIN_IDS:
        txt += (
            "\n<b>👑 ADMINISTRATOR OVERRIDE:</b>\n"
            "🎁 <code>/add #Name 30d</code> - Grant Premium\n"
            "✂️ <code>/rem_prem #Name</code> - Revoke Premium\n"
            "🔇 <code>/mute [#Name] [days] [reason]</code> - Silence User\n"
            "🔊 <code>/unmute [#Name]</code> - Remove Silence\n"
            "🔨 <code>/ban [#Name] [days] [reason]</code> - Exclude User\n"
            "🕊️ <code>/unban [#Name]</code> - Pardon User\n"
            "🔒 <code>/restrict on/off</code> - Toggle Media Protection\n"
            "🗑️ <code>/binch [id]</code> - Configure Backup Archive\n"
            "⏱️ <code>/pmdlt on [secs]</code> - Configure Auto-Purge\n"
            "⚙️ <code>/ref on/off</code> - Initialize Referral Setup\n"
            "📈 <code>/stats</code> - View Diagnostics\n"
            "🚦 <code>/wait on/off</code> - Toggle Network Entry\n"
            "📢 <code>/broadcast</code> - Mass Data Injection (Reply)\n"
            "💬 <code>/chat on/off</code> - Toggle Public Channel"
        )
    await message.reply(txt)

@Client.on_message(filters.command("mute") & filters.user(Config.ADMIN_IDS))
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
            if match:
                nick = match.group(1).strip()
            args = message.command[1:]
            
        if not nick:
            return await message.reply("❌ <b>Error:</b> Please reply to a message or use `/mute #Nickname`.")
            
        u = await db.get_user_by_nickname(nick)
        if not u:
            return await message.reply(f"❌ <b>Error:</b> Identity #{nick} not found.")
            
        if u['user_id'] in Config.ADMIN_IDS:
            return await message.reply("❌ <b>Action Denied:</b> Administrators possess system immunity and cannot be restricted.")
            
        days, reason = 1, "Violation of Network Guidelines"
        
        if len(args) > 0 and args[0].isdigit():
            days = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0:
            reason = " ".join(args)
            
        await db.mute_user(u['user_id'], days * 24)
        await message.reply(f"🔇 <b>Target Silenced:</b> #{nick}\n⏳ <b>Duration:</b> {days} Days\n📝 <b>Reason:</b> {reason}")
        
        try:
            await client.send_message(
                u['user_id'], 
                f"🔇 <b>System Alert: You have been MUTED for {days} days.</b>\n📝 <b>Reason:</b> {reason}\n<i>Transmitting and receiving media has been temporarily disabled.</i>"
            )
        except:
            pass
            
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("unmute") & filters.user(Config.ADMIN_IDS))
async def unmute_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"):
            nick = message.command[1].replace("#", "")
        elif message.reply_to_message:
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match:
                nick = match.group(1).strip()
                
        if not nick:
            return await message.reply("❌ <b>Error:</b> Please reply to a message or use `/unmute #Nickname`.")
            
        u = await db.get_user_by_nickname(nick)
        if not u:
            return await message.reply("❌ <b>Error:</b> User record not found.")
            
        await db.unmute_user(u['user_id'])
        await message.reply(f"🔊 <b>Silence Revoked:</b> #{u['nickname']}")
        
        try:
            await client.send_message(u['user_id'], "🔊 <b>Your account restrictions have been lifted. Welcome back to the network.</b>")
        except:
            pass
            
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("ban") & filters.user(Config.ADMIN_IDS))
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
            if match:
                nick = match.group(1).strip()
            args = message.command[1:]
            
        if not nick:
            return await message.reply("❌ <b>Error:</b> Please reply to a message or use `/ban #Nickname`.")
            
        u = await db.get_user_by_nickname(nick)
        if not u:
            return await message.reply(f"❌ <b>Error:</b> Identity #{nick} not found.")
            
        if u['user_id'] in Config.ADMIN_IDS:
            return await message.reply("❌ <b>Action Denied:</b> Administrators possess system immunity and cannot be banished.")
            
        days, reason = 365, "Severe Protocol Violation"
        
        if len(args) > 0 and args[0].isdigit():
            days = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0:
            reason = " ".join(args)
            
        await db.ban_user(u['user_id'], days)
        await message.reply(f"🔨 <b>Target Banished:</b> #{nick}\n⏳ <b>Duration:</b> {days} Days\n📝 <b>Reason:</b> {reason}")
        
        try:
            await client.send_message(u['user_id'], f"🚨 <b>CRITICAL ALERT: Your network access has been permanently revoked for {days} days.</b>\n📝 <b>Reason:</b> {reason}")
        except:
            pass
            
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("unban") & filters.user(Config.ADMIN_IDS))
async def unban_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"):
            nick = message.command[1].replace("#", "")
        elif message.reply_to_message:
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match:
                nick = match.group(1).strip()
                
        if not nick:
            return await message.reply("❌ <b>Error:</b> Please reply to a message or use `/unban #Nickname`.")
            
        u = await db.get_user_by_nickname(nick)
        if not u:
            return await message.reply("❌ <b>Error:</b> User record not found.")
            
        await db.unban_user(u['user_id'])
        await message.reply(f"🕊️ <b>Target Pardoned:</b> #{u['nickname']}")
        
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("chat") & filters.user(Config.ADMIN_IDS))
async def toggle_chat(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("💬 <b>Syntax:</b> `/chat on` or `/chat off`")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"chat_enabled": mode})
        await message.reply(f"💬 Global Chat Protocol is now: <b>{'ONLINE' if mode else 'OFFLINE'}</b>")
        
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("stats") & filters.user(Config.ADMIN_IDS))
async def stats_cmd(client, message):
    try:
        t, a, b = await db.get_stats()
        await message.reply(f"📊 <b>System Diagnostics:</b>\n👥 Total Identities: {t}\n🟢 Active Nodes: {a}\n🔴 Banished Entities: {b}\n⏱ Core Uptime: {get_uptime()}")
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("add") & filters.user(Config.ADMIN_IDS))
async def manual_add(client, message):
    try:
        if len(message.command) < 3:
            return await message.reply("🎁 <b>Syntax:</b> `/add #Nickname 30d`")
            
        nick = message.command[1].replace("#", "")
        dur = parse_duration(message.command[2])
        u = await db.get_user_by_nickname(nick)
        
        if not u:
            return await message.reply(f"❌ <b>Error:</b> Identity #{nick} does not exist.")
            
        if dur:
            await users.update_one({"user_id": u['user_id']}, {"$set": {"is_premium": True, "premium_expiry": datetime.now() + dur}})
            await message.reply(f"✅ <b>VIP Credentials Granted:</b> #{nick} for {message.command[2]}")
            try:
                await client.send_message(u['user_id'], "💎 <b>VIP Premium Status Acquired!</b> You now have unlimited, zero-delay access.")
            except:
                pass
        else:
            await message.reply("❌ <b>Error:</b> Invalid time parameter (acceptable: 1d, 30m, 1h).")
            
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("rem_prem") & filters.user(Config.ADMIN_IDS))
async def rem_prem_cmd(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("✂️ <b>Syntax:</b> `/rem_prem #Nickname`")
            
        nick = message.command[1].replace("#", "")
        u = await db.get_user_by_nickname(nick)
        
        if not u:
            return await message.reply(f"❌ <b>Error:</b> Identity #{nick} does not exist.")
            
        await db.remove_premium(u['user_id'])
        await message.reply(f"✅ <b>VIP Credentials Revoked:</b> #{nick}")
        try:
            await client.send_message(u['user_id'], "⚠️ <b>WARNING: YOUR VIP ACCESS HAS BEEN TERMINATED BY COMMAND CENTER.</b>")
        except:
            pass
            
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("restrict") & filters.user(Config.ADMIN_IDS))
async def restrict_cmd(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("🔒 <b>Syntax:</b> `/restrict on` or `/restrict off`")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"media_restriction": mode})
        await message.reply(f"✅ <b>Media Forwarding Protection:</b> {'ENGAGED' if mode else 'DISENGAGED'}")
        
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("binch") & filters.user(Config.ADMIN_IDS))
async def set_bin(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("🗑️ <b>Syntax:</b> `/binch -100xxxxxxxx`")
            
        cid = int(message.command[1]) if message.command[1].lstrip('-').isdigit() else message.command[1]
        await db.update_settings({"bin_channel": cid})
        await message.reply(f"✅ <b>Backup Archive Re-routed to:</b> {cid}")
        
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("wait") & filters.user(Config.ADMIN_IDS))
async def wait_cmd(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("🚦 <b>Syntax:</b> `/wait on` (Lock) or `/wait off` (Open)")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"registration_open": not mode})
        await message.reply(f"✅ <b>Network Entry Lock:</b> {'ACTIVE' if mode else 'DISABLED'}")
        
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("pmdlt") & filters.user(Config.ADMIN_IDS))
async def toggle_dlt(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("⏱️ <b>Syntax:</b> `/pmdlt on 60` or `/pmdlt off`")
            
        mode = message.command[1].lower() == "on"
        await db.update_settings({"pm_dlt": mode})
        
        if mode and len(message.command) >= 3:
            await db.update_settings({"dlt_time": int(message.command[2])})
            
        await message.reply(f"✅ <b>Auto-Purge Protocol:</b> {'ONLINE' if mode else 'OFFLINE'}")
        
    except Exception as e:
        await message.reply(f"❌ <b>System Fault:</b> {e}")

@Client.on_message(filters.command("ref") & filters.user(Config.ADMIN_IDS))
async def ref_cmd_init(client, message):
    if len(message.command) < 2:
        return await message.reply("⚙️ <b>Syntax:</b> `/ref on` or `/ref off`")
        
    if message.command[1].lower() == "off":
        await db.update_settings({"ref_system": False})
        return await message.reply("✅ <b>Referral System Offline.</b>")
        
    admin_states[message.from_user.id] = {"step": "ref_1"}
    await message.reply("🔢 <b>Initiating Setup:</b> Enter the required number of referrals for a reward.")

@Client.on_message(filters.text & filters.user(Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "binch", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "join", "me", "register", "referral", "chat"]))
async def admin_state_handler(client, message):
    uid = message.from_user.id
    if uid not in admin_states:
        return
        
    state = admin_states[uid]
    
    if state.get("step") == "ref_1":
        try:
            state["count"] = int(message.text)
            state["step"] = "ref_2"
            await message.reply("📝 <b>Step 2:</b> Provide the custom invitation text (HTML supported).")
        except ValueError:
            await message.reply("❌ <b>Invalid Input:</b> Please provide a numeric value.")
            
    elif state.get("step") == "ref_2":
        state["text"] = message.text.html
        state["step"] = "ref_3"
        await message.reply("⏱ <b>Final Step:</b> Provide the premium duration reward (e.g., 7d, 1M, 24h).")
        
    elif state.get("step") == "ref_3":
        if parse_duration(message.text):
            await db.update_settings({
                "ref_system": True, 
                "ref_count": state["count"], 
                "ref_text": state["text"], 
                "ref_time_str": message.text
            })
            admin_states.pop(uid, None)
            await message.reply("✅ <b>Referral Protocol Configuration Complete. System is now active.</b>")
        else:
            await message.reply("❌ <b>Invalid Formatting:</b> Please utilize proper syntax (e.g., 7d, 1M).")
