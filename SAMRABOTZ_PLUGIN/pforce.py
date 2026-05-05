import random
import re
import logging
from pyrogram import Client, filters, enums
from pyrogram.errors import UserNotParticipant
import config
from database import db

logger = logging.getLogger("PFORCE")

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
        await client.send_message(
            user_id, 
            "<blockquote>"
            "✅ <b>Join request registered</b>\n"
            "\n"
            "You now have access. Please type /start to continue."
            "</blockquote>"
        )
    except Exception as e: 
        logger.error(f"Failed to notify user {user_id} of join request approval: {str(e)}", exc_info=True)

async def check_fsub(client, user_id):
    user = await db.get_user(user_id) or {}
    requested_channels = user.get("requested_channels", [])
    missing_channels = []
    error_status = None
    target_channels = []

    if config.Config.FORCE_SUB_CHANNEL:
        target_channels.append(config.Config.FORCE_SUB_CHANNEL)
    if config.Config.PENDING_RQUST_CHNL_ID:
        raw_ids = re.split(r'[,\s]+', config.Config.PENDING_RQUST_CHNL_ID.strip())
        for rid in raw_ids:
            if rid: target_channels.append(rid.strip())

    for x in target_channels:
        chat_id = x
        if isinstance(chat_id, str):
            if chat_id.startswith("-100") and chat_id.replace("-", "").isdigit(): chat_id = int(chat_id)
            elif not chat_id.startswith("@") and not chat_id.lstrip("-").isdigit(): chat_id = f"@{chat_id}"

        if chat_id in requested_channels: continue

        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]: 
                raise UserNotParticipant()
        except UserNotParticipant:
            try:
                if chat_id not in config.invite_links_cache:
                    chat = await client.get_chat(chat_id)
                    link = await client.create_chat_invite_link(chat_id, creates_join_request=True)
                    config.invite_links_cache[chat_id] = {"url": link.invite_link, "title": chat.title if chat.title else "Network Channel"}
                cache_data = config.invite_links_cache[chat_id]
                missing_channels.append({"text": f"Request to Join {cache_data['title']}", "url": cache_data['url']})
            except Exception as e: 
                logger.error(f"Failed to fetch invite link for {chat_id}: {str(e)}", exc_info=True)
                error_status = "not_admin"
        except Exception as e:
            if "chat_admin_required" in str(e).lower(): 
                error_status = "not_admin"
            else:
                logger.error(f"Error checking sub status for {user_id} in {chat_id}: {str(e)}", exc_info=True)

    if error_status: return False, "not_admin"
    if missing_channels: return False, missing_channels
    return True, None
