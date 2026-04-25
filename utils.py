import re
import time
from datetime import datetime, timedelta
from pyrogram import enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import ChatAdminRequired, UserNotParticipant
from config import Config, START_TEXT_TEMPLATE, START_TIME
from database import db

async def check_fsub(client, user_id):
    config = await db.get_bot_settings()
    user = await db.get_user(user_id) or {}
    requested_channels = user.get("requested_channels", [])
    
    missing_channels = []
    error_status = None
    
    if Config.FORCE_SUB_CHANNEL:
        chat_id = Config.FORCE_SUB_CHANNEL
        if isinstance(chat_id, str):
            if chat_id.startswith("-100") and chat_id.replace("-", "").isdigit():
                chat_id = int(chat_id)
            elif not chat_id.startswith("@") and not chat_id.lstrip("-").isdigit():
                chat_id = f"@{chat_id}"

        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                raise UserNotParticipant()
        except UserNotParticipant:
            try:
                chat = await client.get_chat(chat_id)
                link = chat.invite_link or await chat.export_invite_link()
                missing_channels.append({"text": "📢 Join Primary Channel", "url": link})
            except Exception:
                error_status = "not_admin"
        except Exception as e:
            if "chat_admin_required" in str(e).lower():
                error_status = "not_admin"
                
    if config.get("frsub_enabled") and config.get("frsub_channels"):
        for cid in config["frsub_channels"]:
            if cid in requested_channels:
                continue
            try:
                member = await client.get_chat_member(cid, user_id)
                if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                    continue
            except UserNotParticipant:
                try:
                    chat = await client.get_chat(cid)
                    link = chat.invite_link
                    if not link:
                        link = await chat.export_invite_link(creates_join_request=True)
                    title = chat.title if chat.title else "Exclusive Channel"
                    missing_channels.append({"text": f"📩 Request to Join {title}", "url": link})
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
    return str(timedelta(seconds=int(time.time() - START_TIME)))

def build_start_text(user):
    time_left = "♾️ Unlimited (Premium)" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    return START_TEXT_TEMPLATE.format(name=user['nickname'], time=time_left, status="👑 VIP" if user.get('is_premium') else "🆓 Free")

def start_keyboard(is_ref_on=False):
    buttons = [
        [InlineKeyboardButton("📜 Rules", callback_data="show_rules"), InlineKeyboardButton("⏳ Status", callback_data="show_status")]
    ]
    if is_ref_on:
        buttons.append([InlineKeyboardButton("👥 Refer Friends & Get Premium", callback_data="show_referral")])
    buttons.append([InlineKeyboardButton("🔄 Refresh Dashboard", callback_data="refresh_start")])
    return InlineKeyboardMarkup(buttons)

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_start")]])

def ref_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh Points", callback_data="refresh_ref"), InlineKeyboardButton("🔙 Back", callback_data="back_start")]
    ])
