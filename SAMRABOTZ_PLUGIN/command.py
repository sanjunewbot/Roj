import random
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from database import db, users
from utils import parse_duration, start_keyboard, history_reply_keyboard, get_time_left
from SAMRABOTZ_PLUGIN.pforce import check_fsub, ADJECTIVES, NOUNS

logger = logging.getLogger("COMMAND")

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    bot_config = await db.get_bot_settings()
    user = await db.get_user(user_id)
    
    if not user and not bot_config.get('registration_open', True): 
        return await message.reply("> 🚫 <b>Registration locked</b>\n> \n> Registration is currently locked by administrators.")
        
    if len(message.command) > 1 and message.command[1].startswith("ref_"):
        try:
            inviter_id = int(message.command[1].split("_")[1])
            if inviter_id != user_id and not user and bot_config.get('ref_system'):
                await users.update_one({"user_id": inviter_id}, {"$inc": {"ref_balance": 1}})
                inviter = await db.get_user(inviter_id)
                try: 
                    await client.send_message(inviter_id, f"> 🎉 <b>New referral</b>\n> \n> Points accumulated: {inviter['ref_balance']}/{bot_config['ref_count']}")
                except Exception as e: 
                    logger.error(f"Failed to send referral alert to {inviter_id}: {str(e)}", exc_info=True)
                    
                if inviter['ref_balance'] >= bot_config['ref_count']:
                    duration = parse_duration(bot_config['ref_time_str'])
                    if duration:
                        expiry = datetime.now() + duration
                        await users.update_one({"user_id": inviter_id}, {"$set": {"is_premium": True, "premium_expiry": expiry}, "$inc": {"ref_balance": -bot_config['ref_count']}})
                        try: 
                            await client.send_message(inviter_id, "> 🎊 <b>VIP premium activated</b>\n> \n> Your referral reward has been credited.")
                        except Exception as e: 
                            logger.error(f"Failed to send premium activation alert to {inviter_id}: {str(e)}", exc_info=True)
        except Exception as e: 
            logger.error(f"Referral processing error for user {user_id}: {str(e)}", exc_info=True)
            
    if not user:
        random_name = f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(1000, 9999)}"
        await db.add_user(user_id, random_name)
        user = await db.get_user(user_id)
        
    is_joined, result = await check_fsub(client, user_id)
    if not is_joined:
        if result == "not_admin": 
            return await message.reply("> ⚠️ <b>System error</b>\n> \n> Bot is not an admin in the mandatory channel(s).")
        buttons = []
        for item in result: 
            buttons.append([InlineKeyboardButton(item["text"], url=item["url"])])
        return await message.reply("> ❌ <b>Access denied</b>\n> \n> You must join or send join requests to all mandatory networks below.\n> \n> <i>Note: Once requested, come back and type /start</i>", reply_markup=InlineKeyboardMarkup(buttons))
        
    time_val = "Unlimited VIP" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    status_val = "VIP Premium" if user.get('is_premium') else "Standard Free"
    bot_info = client.me
    
    welcome_msg = (
        f"> 🔥 <b>Welcome to the elite network</b>\n"
        f"> \n"
        f"> Greetings, #{user['nickname']}! We are glad to have you here.\n"
        f"> \n"
        f"> 🤖 <b>Bot identity:</b> @{bot_info.username}\n"
        f"> ⚡ <b>System vibe:</b> Fast, secure, and advanced.\n"
        f"> \n"
        f"> ⏳ <b>Account time remaining:</b> {time_val}\n"
        f"> 💎 <b>Current status:</b> {status_val}\n"
        f"> \n"
        f"> 📩 <b>Join now:</b> <a href='https://t.me/roomjoinus'>@roomjoinus</a>"
    )
    t_link = bot_config.get("tutorial_link")
    await message.reply(welcome_msg, reply_markup=start_keyboard(bot_config.get('ref_system'), t_link), disable_web_page_preview=True)
    
    menu_msg = "> 🎛 <b>Keyboard deployed</b> 👇"
    await message.reply(menu_msg, reply_markup=history_reply_keyboard(bot_config.get('get_btn_enabled')))

@Client.on_message(filters.command("register") & filters.private)
async def register_cmd(client, message):
    is_joined, _ = await check_fsub(client, message.from_user.id)
    if not is_joined: return
    if len(message.command) < 2: 
        return await message.reply("> 📝 <b>Format instruction</b>\n> \n> Use <code>/register [NewName]</code> to update your identity.")
        
    await users.update_one({"user_id": message.from_user.id}, {"$set": {"nickname": message.command[1]}})
    await message.reply(f"> ✅ <b>Identity updated</b>\n> \n> Your anonymous identity has been updated to <b>{message.command[1]}</b>.")

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    txt = (
        "> 🛠 <b>Bot command directory</b>\n"
        "> \n"
        "> 👤 <b>User commands</b>\n"
        "> ✦ /start ➤ Dashboard & status\n"
        "> ✦ /me ➤ Detailed profile stats\n"
        "> ✦ /register [name] ➤ Update identity\n"
        "> ✦ /referral ➤ Earn VIP access\n"
        "> ✦ /plans ➤ View plans & benefits\n"
        "> ✦ /help ➤ Open command menu\n"
        "> \n"
    )
    if message.from_user.id in config.Config.ADMIN_IDS:
        txt += (
            "> 👑 <b>Admin commands</b>\n"
            "> ✦ /stats ➤ Live system diagnostics\n"
            "> ✦ /add #name 30d ➤ Grant premium\n"
            "> ✦ /rem_prem #name ➤ Remove premium\n"
            "> ✦ /mute #name [days] [reason] ➤ Mute user\n"
            "> ✦ /unmute #name ➤ Unmute user\n"
            "> ✦ /ban #name [days] [reason] ➤ Ban user\n"
            "> ✦ /unban #name ➤ Unban user\n"
            "> ✦ /broadcast ➤ Global message (reply)\n"
            "> ✦ /chat on/off ➤ Global chat toggle\n"
            "> ✦ /restrict on/off ➤ Protection mode\n"
            "> ✦ /binch [id] ➤ Set backup bin\n"
            "> ✦ /wait on/off ➤ Registration lock\n"
            "> ✦ /pmdlt on [secs] ➤ Auto purge setup\n"
            "> ✦ /ref on/off ➤ Referral config\n"
            "> ✦ /get_buttn on/off ➤ Media history\n"
            "> ✦ /tutorial on/off ➤ Video guide\n"
            "> \n"
        )
    txt += (
        "> 📩 <b>Join now:</b> <a href='https://t.me/roomjoinus'>@roomjoinus</a>\n"
        "> 🚀 <b>System:</b> Elite bot system • Fast • Secure • Advanced"
    )
    await message.reply(txt, disable_web_page_preview=True)
