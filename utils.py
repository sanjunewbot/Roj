import re
import time
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import config

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

def get_uptime():
    return str(timedelta(seconds=int(time.time() - config.START_TIME)))

def start_keyboard(is_ref_on=False, t_link=None):
    buttons = [
        [InlineKeyboardButton("Rules", callback_data="show_rules"), InlineKeyboardButton("Status", callback_data="show_status")]
    ]
    if is_ref_on: buttons.append([InlineKeyboardButton("Referral Network", callback_data="show_referral")])
    if t_link: buttons.append([InlineKeyboardButton("How to Use", url=t_link)])
    buttons.append([InlineKeyboardButton("Refresh Dashboard", callback_data="refresh_start")])
    return InlineKeyboardMarkup(buttons)

def history_reply_keyboard(is_get_btn_on=False):
    if is_get_btn_on: return ReplyKeyboardMarkup([[KeyboardButton("GET MEDIA HISTORY")]], resize_keyboard=True)
    return ReplyKeyboardRemove()

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Back to Main Menu", callback_data="back_start")]])

def ref_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Refresh Points", callback_data="refresh_ref"), InlineKeyboardButton("Back to Main Menu", callback_data="back_start")]])
