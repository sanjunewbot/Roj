import re
import time
import logging
import aiohttp
from datetime import datetime, timedelta
import config

logger = logging.getLogger("UTILS")

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

async def send_raw_api_message(chat_id, text, buttons=None, reply_markup=None):
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    elif reply_markup:
         payload["reply_markup"] = reply_markup

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"API Error (sendMessage): {await response.text()}")
                return await response.json()
        except Exception as e:
            logger.error(f"Exception in send_raw_api_message: {str(e)}", exc_info=True)
            return None

async def edit_raw_api_message(chat_id, message_id, text, buttons=None):
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"API Error (editMessageText): {await response.text()}")
                return await response.json()
        except Exception as e:
            logger.error(f"Exception in edit_raw_api_message: {str(e)}", exc_info=True)
            return None

async def copy_raw_api_message(chat_id, from_chat_id, message_id, caption=None, buttons=None, protect_content=False):
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/copyMessage"
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        "parse_mode": "HTML",
        "protect_content": protect_content
    }
    if caption is not None:
        payload["caption"] = caption
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"API Error (copyMessage): {await response.text()}")
                return await response.json()
        except Exception as e:
            logger.error(f"Exception in copy_raw_api_message: {str(e)}", exc_info=True)
            return None

async def send_raw_api_media(chat_id, media_id, media_type, caption=None, buttons=None, protect_content=False):
    endpoint = "sendPhoto" if media_type == "photo" else "sendVideo"
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/{endpoint}"
    payload = {
        "chat_id": chat_id,
        media_type: media_id,
        "parse_mode": "HTML",
        "protect_content": protect_content
    }
    if caption:
        payload["caption"] = caption
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"API Error ({endpoint}): {await response.text()}")
                return await response.json()
        except Exception as e:
            logger.error(f"Exception in send_raw_api_media: {str(e)}", exc_info=True)
            return None

def start_keyboard(is_ref_on=False, t_link=None):
    buttons = [
        [{"text": "Rules", "callback_data": "show_rules", "style": "primary"}, {"text": "Status", "callback_data": "show_status", "style": "success"}]
    ]
    if is_ref_on: buttons.append([{"text": "Referral Network", "callback_data": "show_referral", "style": "success"}])
    if t_link: buttons.append([{"text": "How to Use", "url": t_link, "style": "primary"}])
    buttons.append([{"text": "Refresh Dashboard", "callback_data": "refresh_start", "style": "danger"}])
    return buttons

def history_reply_keyboard(is_get_btn_on=False):
    if is_get_btn_on: return {"keyboard": [[{"text": "GET MEDIA HISTORY"}]], "resize_keyboard": True}
    return {"remove_keyboard": True}

def back_keyboard():
    return [[{"text": "Back to Main Menu", "callback_data": "back_start", "style": "primary"}]]

def ref_keyboard():
    return [[{"text": "Refresh Points", "callback_data": "refresh_ref", "style": "success"}, {"text": "Back to Main Menu", "callback_data": "back_start", "style": "danger"}]]
