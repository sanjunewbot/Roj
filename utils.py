import re, time
from datetime import datetime, timedelta
from pyrogram import enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config, START_TEXT_TEMPLATE, START_TIME
async def check_fsub(client, user_id):
    try:
        member = await client.get_chat_member(Config.FORCE_SUB_CHANNEL, user_id)
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]: return True
    except: pass
    return False
def parse_duration(duration_str):
    match = re.match(r"(\d+)([mhdM])", duration_str)
    if not match: return None
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
def get_uptime(): return str(timedelta(seconds=int(time.time() - START_TIME)))
def build_start_text(user):
    time_left = "Unlimited (Premium)" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    return START_TEXT_TEMPLATE.format(name=user['nickname'], time=time_left)
def start_keyboard(is_ref_on=False):
    buttons = [[InlineKeyboardButton("📜 Rules", callback_data="show_rules"), InlineKeyboardButton("⏳ Status", callback_data="show_status")]]
    if is_ref_on: buttons.append([InlineKeyboardButton("👥 Refer Get Premium", callback_data="show_referral")])
    buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_start")])
    return InlineKeyboardMarkup(buttons)
def back_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_start")]])
def ref_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh Points", callback_data="refresh_ref"), InlineKeyboardButton("🔙 Back", callback_data="back_start")]])
