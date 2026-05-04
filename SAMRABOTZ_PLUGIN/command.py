import random
import logging
from datetime import datetime
from pyrogram import Client, filters
import config
from database import db, users
from utils import parse_duration, start_keyboard, history_reply_keyboard, get_time_left, send_raw_api_message
from SAMRABOTZ_PLUGIN.pforce import check_fsub, ADJECTIVES, NOUNS

logger = logging.getLogger("COMMAND")

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    bot_config = await db.get_bot_settings()
    user = await db.get_user(user_id)

    if not user and not bot_config.get('registration_open', True): 
        return await message.reply(
            "<blockquote>"
            "🚫 <b>Registration locked</b>
"
            "
"
            "Registration is currently locked by administrators."
            "</blockquote>"
        )

    if len(message.command) > 1 and message.command[1].startswith("ref_"):
        try:
            inviter_id = int(message.command[1].split("_")[1])
            if inviter_id != user_id and not user and bot_config.get('ref_system'):
                await users.update_one({"user_id": inviter_id}, {"$inc": {"ref_balance": 1}})
                inviter = await db.get_user(inviter_id)
                try: 
                    await client.send_message(
                        inviter_id, 
                        "<blockquote>"
                        f"🎉 <b>New referral</b>
"
                        "
"
                        f"Points accumulated: {inviter['ref_balance']}/{bot_config['ref_count']}"
                        "</blockquote>"
                    )
                except Exception as e: 
                    logger.error(f"Failed to send referral alert to {inviter_id}: {str(e)}", exc_info=True)

                if inviter['ref_balance'] >= bot_config['ref_count']:
                    duration = parse_duration(bot_config['ref_time_str'])
                    if duration:
                        expiry = datetime.now() + duration
                        await users.update_one({"user_id": inviter_id}, {"$set": {"is_premium": True, "premium_expiry": expiry}, "$inc": {"ref_balance": -bot_config['ref_count']}})
                        try: 
                            await client.send_message(
                                inviter_id, 
                                "<blockquote>"
                                "🎊 <b>VIP premium activated</b>
"
                                "
"
                                "Your referral reward has been credited."
                                "</blockquote>"
                            )
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
            return await send_raw_api_message(
                user_id, 
                "<blockquote>"
                "⚠️ <b>System error</b>
"
                "
"
                "Bot is not an admin in the mandatory channel(s)."
                "</blockquote>"
            )
        buttons = []
        for item in result: 
            buttons.append([{"text": item["text"], "url": item["url"], "style": "danger"}])
        return await send_raw_api_message(
            user_id, 
            "<blockquote>"
            "❌ <b>Access denied</b>
"
            "
"
            "You must join or send join requests to all mandatory networks below.
"
            "
"
            "<i>Note: Once requested, come back and type /start</i>"
            "</blockquote>", 
            buttons=buttons
        )

    time_val = "Unlimited VIP" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    status_val = "VIP Premium" if user.get('is_premium') else "Standard Free"
    bot_info = client.me

    welcome_msg = (
        "<blockquote>"
        f"🔥 <b>Welcome to the elite network</b>
"
        f"
"
        f"Greetings, #{user['nickname']}! We are glad to have you here.
"
        f"
"
        f"🤖 <b>Bot identity:</b> @{bot_info.username}
"
        f"⚡ <b>System vibe:</b> Fast, secure, and advanced.
"
        f"
"
        f"⏳ <b>Account time remaining:</b> {time_val}
"
        f"💎 <b>Current status:</b> {status_val}
"
        f"
"
        f"📩 <b>Join now:</b> <a href='https://t.me/roomjoinus'>@roomjoinus</a>"
        "</blockquote>"
    )
    t_link = bot_config.get("tutorial_link")
    await send_raw_api_message(user_id, welcome_msg, buttons=start_keyboard(bot_config.get('ref_system'), t_link))

    menu_msg = (
        "<blockquote>"
        "🎛 <b>Keyboard deployed</b> 👇"
        "</blockquote>"
    )
    await send_raw_api_message(user_id, menu_msg, reply_markup=history_reply_keyboard(bot_config.get('get_btn_enabled')))

@Client.on_message(filters.command("register") & filters.private)
async def register_cmd(client, message):
    is_joined, _ = await check_fsub(client, message.from_user.id)
    if not is_joined: return
    if len(message.command) < 2: 
        return await message.reply(
            "<blockquote>"
            "📝 <b>Format instruction</b>
"
            "
"
            "Use <code>/register [NewName]</code> to update your identity."
            "</blockquote>"
        )

    user_id = message.from_user.id
    new_name = message.command[1]
    user = await db.get_user(user_id)

    if not user:
        await db.add_user(user_id, new_name)
    else:
        await users.update_one({"user_id": user_id}, {"$set": {"nickname": new_name}})

    await message.reply(
        "<blockquote>"
        f"✅ <b>Identity updated</b>
"
        "
"
        f"Your anonymous identity has been updated to <b>{new_name}</b>."
        "</blockquote>"
    )

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    txt = (
        "<blockquote>"
        "🛠 <b>Bot command directory</b>
"
        "
"
        "👤 <b>User commands</b>
"
        "✦ /start ➤ Dashboard & status
"
        "✦ /me ➤ Detailed profile stats
"
        "✦ /register [name] ➤ Update identity
"
        "✦ /referral ➤ Earn VIP access
"
        "✦ /plans ➤ View plans & benefits
"
        "✦ /help ➤ Open command menu
"
        "
"
        "</blockquote>"
    )
    if message.from_user.id in config.Config.ADMIN_IDS:
        txt += (
            "<blockquote>"
            "👑 <b>Admin commands</b>
"
            "✦ /stats ➤ Live system diagnostics
"
            "✦ /add #name 30d ➤ Grant premium
"
            "✦ /rem_prem #name ➤ Remove premium
"
            "✦ /mute #name [days] [reason] ➤ Mute user
"
            "✦ /unmute #name ➤ Unmute user
"
            "✦ /ban #name [days] [reason] ➤ Ban user
"
            "✦ /unban #name ➤ Unban user
"
            "✦ /broadcast ➤ Global message (reply)
"
            "✦ /chat on/off ➤ Global chat toggle
"
            "✦ /restrict on/off ➤ Protection mode
"
            "✦ /binch [id] ➤ Set backup bin
"
            "✦ /wait on/off ➤ Registration lock
"
            "✦ /pmdlt on [secs] ➤ Auto purge setup
"
            "✦ /ref on/off ➤ Referral config
"
            "✦ /get_buttn on/off ➤ Media history
"
            "✦ /tutorial on/off ➤ Video guide
"
            "
"
            "</blockquote>"
        )
    txt += (
        "<blockquote>"
        "📩 <b>Join now:</b> <a href='https://t.me/roomjoinus'>@roomjoinus</a>
"
        "🚀 <b>System:</b> Elite bot system • Fast • Secure • Advanced"
        "</blockquote>"
    )
    await message.reply(txt, disable_web_page_preview=True)
