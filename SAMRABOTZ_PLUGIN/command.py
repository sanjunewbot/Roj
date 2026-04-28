import random
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from database import db, users
from utils import parse_duration, start_keyboard, history_reply_keyboard, get_time_left
from SAMRABOTZ_PLUGIN.pforce import check_fsub, ADJECTIVES, NOUNS

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    bot_config = await db.get_bot_settings()
    user = await db.get_user(user_id)
    if not user and not bot_config.get('registration_open', True): return await message.reply("🚫 <b>Registration Locked by Administrators.</b>")
    
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
        if result == "not_admin": return await message.reply("⚠️ <b>System Error:</b> Bot is not an admin in the mandatory channel(s).")
        buttons = []
        for item in result: buttons.append([InlineKeyboardButton(item["text"], url=item["url"])])
        return await message.reply("❌ <b>Access Denied!</b>\nYou must join or send join requests to all mandatory networks below.\n\n<i>Note: Once you request, come back and type /start</i>", reply_markup=InlineKeyboardMarkup(buttons))
        
    time_val = "𝕌ℕ𝕃𝕀𝕄𝕀𝕋𝔼𝔻" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now())).upper()
    status_val = "𝕍𝕀ℙ ℙℝ𝔼𝕄𝕀𝕌𝕄" if user.get('is_premium') else "𝕊𝕋𝔸ℕ𝔻𝔸ℝ𝔻 𝔽ℝ𝔼𝔼"
    bot_info = client.me
    
    welcome_msg = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 𝕎𝔼𝕃ℂ𝕆𝕄𝔼 𝕋𝕆 𝕋ℍ𝔼 𝔼𝕃𝕀𝕋𝔼 ℕ𝔼𝕋𝕎𝕆ℝ𝕂 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"𝔾ℝ𝔼𝔼𝕋𝕀ℕ𝔾𝕊, #{user['nickname'].upper()}! 𝕎𝔼 𝔸ℝ𝔼 𝔾𝕃𝔸𝔻 𝕋𝕆 ℍ𝔸𝕍𝔼 𝕐𝕆𝕌 ℍ𝔼ℝ𝔼.\n\n"
        f"🤖 𝔹𝕆𝕋 𝕀𝔻𝔼ℕ𝕋𝕀𝕋𝕐: @{bot_info.username.upper()}\n"
        "⚡ 𝕊𝕐𝕊𝕋𝔼𝕄 𝕍𝕀𝔹𝔼: 𝔽𝔸𝕊𝕋, 𝕊𝔼ℂ𝕌ℝ𝔼, 𝔸ℕ𝔻 𝔸𝔻𝕍𝔸ℕℂ𝔼𝔻.\n\n"
        f"⏳ 𝔸ℂℂ𝕆𝕌ℕ𝕋 𝕋𝕀𝕄𝔼 ℝ𝔼𝕄𝔸𝕀ℕ𝕀ℕ𝔾: <b>{time_val}</b>\n"
        f"💎 ℂ𝕌ℝℝ𝔼ℕ𝕋 𝕊𝕋𝔸𝕋𝕌𝕊: <b>{status_val}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📩 𝕁𝕆𝕀ℕ ℕ𝕆𝕎: <a href='https://t.me/roomjoinus'>@roomjoinus</a>"
    )
    t_link = bot_config.get("tutorial_link")
    await message.reply(welcome_msg, reply_markup=start_keyboard(bot_config.get('ref_system'), t_link), disable_web_page_preview=True)
    menu_msg = "🎛 <b>KEYBOARD DEPLOYED 👇</b>"
    await message.reply(menu_msg, reply_markup=history_reply_keyboard(bot_config.get('get_btn_enabled')))

@Client.on_message(filters.command("register") & filters.private)
async def register_cmd(client, message):
    is_joined, _ = await check_fsub(client, message.from_user.id)
    if not is_joined: return
    if len(message.command) < 2: return await message.reply("📝 <b>Format:</b> `/register [NewName]`")
    await users.update_one({"user_id": message.from_user.id}, {"$set": {"nickname": message.command[1]}})
    await message.reply(f"✅ Your anonymous identity has been updated to '<b>{message.command[1]}</b>'.")

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    txt = (
        "╔═══━━━─── • ───━━━═══╗\n\n"
        "🛠 <b>BOT COMMAND DIRECTORY</b>\n\n"
        "╚═══━━━─── • ───━━━═══╝\n"
        "╭─👤 <b>USER COMMANDS</b>\n\n"
        "│ ✦ /START ➤ DASHBOARD & STATUS\n\n"
        "│ ✦ /ME ➤ DETAILED PROFILE STATS\n\n"
        "│ ✦ /REGISTER [NAME] ➤ UPDATE IDENTITY\n\n"
        "│ ✦ /REFERRAL ➤ EARN VIP ACCESS\n\n"
        "│ ✦ /PLANS ➤ VIEW PLANS & BENEFITS\n\n"
        "│ ✦ /HELP ➤ OPEN COMMAND MENU\n\n"
        "╰───────────────────────\n"
    )
    if message.from_user.id in config.Config.ADMIN_IDS:
        txt += (
            "╭─👑 <b>ADMIN COMMANDS</b>\n\n"
            "│ ✦ /STATS ➤ LIVE SYSTEM DIAGNOSTICS\n\n"
            "│ ✦ /ADD #NAME 30D ➤ GRANT PREMIUM\n\n"
            "│ ✦ /REM_PREM #NAME ➤ REMOVE PREMIUM\n\n"
            "│ ✦ /MUTE #NAME [DAYS] [REASON] ➤ MUTE USER\n\n"
            "│ ✦ /UNMUTE #NAME ➤ UNMUTE USER\n\n"
            "│ ✦ /BAN #NAME [DAYS] [REASON] ➤ BAN USER\n\n"
            "│ ✦ /UNBAN #NAME ➤ UNBAN USER\n\n"
            "│ ✦ /BROADCAST ➤ GLOBAL MESSAGE (REPLY)\n\n"
            "│ ✦ /CHAT ON/OFF ➤ GLOBAL CHAT TOGGLE\n\n"
            "│ ✦ /RESTRICT ON/OFF ➤ PROTECTION MODE\n\n"
            "│ ✦ /BINCH [ID] ➤ SET BACKUP BIN\n\n"
            "│ ✦ /WAIT ON/OFF ➤ REGISTRATION LOCK\n\n"
            "│ ✦ /PMDLT ON [SECS] ➤ AUTO PURGE SETUP\n\n"
            "│ ✦ /REF ON/OFF ➤ REFERRAL CONFIG\n\n"
            "│ ✦ /GET_BUTTN ON/OFF ➤ MEDIA HISTORY\n\n"
            "│ ✦ /TUTORIAL ON/OFF ➤ VIDEO GUIDE\n\n"
            "╰───────────────────────\n"
        )
    txt += (
        "╔═════━──────━═════╗\n\n"
        "📩 𝕁𝕆𝕀ℕ ℕ𝕆𝕎: <a href='https://t.me/roomjoinus'>@roomjoinus</a>\n\n"
        "🚀 ELITE BOT SYSTEM • FAST • SECURE • ADVANCED\n\n"
        "╚═════━──────━═════╝"
    )
    await message.reply(txt, disable_web_page_preview=True)
