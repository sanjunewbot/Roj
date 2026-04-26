import re
import time
from datetime import datetime, timedelta
from pyrogram import enums
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import ChatAdminRequired, UserNotParticipant
import config
from database import db

async def check_fsub(client, user_id):
    bot_config = await db.get_bot_settings()
    user = await db.get_user(user_id) or {}
    requested_channels = user.get("requested_channels", [])
    
    missing_channels = []
    error_status = None
    
    if config.Config.FORCE_SUB_CHANNEL:
        chat_id = config.Config.FORCE_SUB_CHANNEL
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
                if chat_id not in config.invite_links_cache:
                    chat = await client.get_chat(chat_id)
                    link = await client.create_chat_invite_link(chat_id, creates_join_request=True)
                    config.invite_links_cache[chat_id] = {"url": link.invite_link, "title": chat.title if chat.title else "Primary Channel"}
                
                cache_data = config.invite_links_cache[chat_id]
                missing_channels.append({"text": f"📢 Request to Join {cache_data['title']}", "url": cache_data['url']})
            except Exception as e:
                error_status = "not_admin"
        except Exception as e:
            if "chat_admin_required" in str(e).lower():
                error_status = "not_admin"
                
    if config.Config.PENDING_RQUST_CHNL_ID:
        raw_ids = re.split(r'[,\s]+', config.Config.PENDING_RQUST_CHNL_ID.strip())
        for x in raw_ids:
            if not x: continue
            clean_id = x.strip()
            cid = int(clean_id) if clean_id.lstrip('-').isdigit() else clean_id
            
            if cid in requested_channels:
                continue
                
            try:
                member = await client.get_chat_member(cid, user_id)
                if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
                    continue
                else:
                     raise UserNotParticipant()
            except UserNotParticipant:
                try:
                    if cid not in config.invite_links_cache:
                        chat = await client.get_chat(cid)
                        link = await client.create_chat_invite_link(cid, creates_join_request=True)
                        config.invite_links_cache[cid] = {"url": link.invite_link, "title": chat.title if chat.title else "Exclusive Channel"}
                        
                    cache_data = config.invite_links_cache[cid]
                    missing_channels.append({"text": f"📩 Request to Join {cache_data['title']}", "url": cache_data['url']})
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
    time_left = "♾️ Unlimited (Premium)" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    return config.START_TEXT_TEMPLATE.format(name=user['nickname'], time=time_left, status="👑 VIP" if user.get('is_premium') else "🆓 Free")

def start_keyboard(is_ref_on=False, is_get_btn_on=False):
    buttons = []
    row1 = [KeyboardButton("📜 Rules"), KeyboardButton("⏳ Status")]
    buttons.append(row1)
    
    if is_get_btn_on:
        buttons.append([KeyboardButton("🎥 GET MEDIA HISTORY")])
    
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def back_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("🔙 Back to Main Menu")]], resize_keyboard=True)

def ref_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔄 Refresh Points"), KeyboardButton("🔙 Back to Main Menu")]
    ], resize_keyboard=True)