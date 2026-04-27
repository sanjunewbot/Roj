import re
import time
from datetime import datetime, timedelta
from pyrogram import enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from pyrogram.errors import ChatAdminRequired, UserNotParticipant
import config
from database import db

async def check_fsub(client, user_id):
    bot_config = await db.get_bot_settings()
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
            if chat_id.startswith("-100") and chat_id.replace("-", "").isdigit():
                chat_id = int(chat_id)
            elif not chat_id.startswith("@") and not chat_id.lstrip("-").isdigit():
                chat_id = f"@{chat_id}"

        if chat_id in requested_channels:
            continue

        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                raise UserNotParticipant()
        except UserNotParticipant:
            try:
                if chat_id not in config.invite_links_cache:
                    chat = await client.get_chat(chat_id)
                    link = await client.create_chat_invite_link(chat_id, creates_join_request=True)
                    config.invite_links_cache[chat_id] = {
                        "url": link.invite_link, 
                        "title": chat.title if chat.title else "Network Channel"
                    }
                
                cache_data = config.invite_links_cache[chat_id]
                missing_channels.append({"text": f"Request to Join {cache_data['title']}", "url": cache_data['url']})
            except Exception:
                error_status = "not_admin"
        except Exception as e:
            if "chat_admin_required" in str(e).lower():
                error_status = "not_admin"

    if error_status:
        return False, "not_admin"
    if missing_channels:
        return False, missing_channels
        
    return True, None

def parse_duration(duration_str):
    match = re.match(r"(\d+)([mhdM])", duration_str)
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    if unit == 'm': return timedelta(minutes=val)
    elif unit == 'h': return timedelta(hours=val)
    elif unit == 'd': return timedelta(days=val)
    elif unit == 'M': return timedelta(days=val * 30)
    return None

def get_time_left(active_until):
    now = datetime.now()
    if active_until > now:
        mins = int((active_until - now).total_seconds() // 60)
        return f"{mins//60}h {mins%60}m" if mins >= 60 else f"{mins}m"
    return "0m"

def get_uptime():
    return str(timedelta(seconds=int(time.time() - config.START_TIME)))

def build_start_text(user):
    time_left = "Unlimited (Premium)" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    return config.START_TEXT_TEMPLATE.format(name=user['nickname'], time=time_left, status="VIP" if user.get('is_premium') else "Free")

def start_keyboard(is_ref_on=False, t_link=None):
    buttons = [
        [
            InlineKeyboardButton("Rules", callback_data="show_rules"), 
            InlineKeyboardButton("Status", callback_data="show_status")
        ]
    ]
    
    if is_ref_on:
        buttons.append([InlineKeyboardButton("Referral Network", callback_data="show_referral")])
        
    if t_link:
        buttons.append([InlineKeyboardButton("How to Use", url=t_link)])
        
    buttons.append([InlineKeyboardButton("Refresh Dashboard", callback_data="refresh_start")])
    
    return InlineKeyboardMarkup(buttons)

def history_reply_keyboard(is_get_btn_on=False):
    if is_get_btn_on:
        return ReplyKeyboardMarkup([[KeyboardButton("GET MEDIA HISTORY")]], resize_keyboard=True)
    return ReplyKeyboardRemove()

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back to Main Menu", callback_data="back_start")]])

def ref_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Refresh Points", callback_data="refresh_ref"), InlineKeyboardButton("Back to Main Menu", callback_data="back_start")]
    ])
