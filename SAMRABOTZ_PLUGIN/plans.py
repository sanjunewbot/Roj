from pyrogram import Client, filters
from datetime import datetime
import config
from database import db
from utils import get_time_left, send_raw_api_message

@Client.on_message(filters.command("plans") & filters.private)
async def plans_cmd(client, message):
    text = (
        "<blockquote>"
        "💎 <b>VIP PREMIUM PLANS</b> 💎\n"
        "\n"
        "<b>[1] WEEKLY ELITE (7 Days) - ₹30</b>\n"
        "✦ 7 Days of Uninterrupted Access\n"
        "✦ Zero-delay priority delivery (≈10s)\n"
        "✦ No media sharing required to stay active\n"
        "\n"
        "<b>[2] MONTHLY SUPREME (30 Days) - ₹150</b>\n"
        "✦ 30 Days of Complete Freedom\n"
        "✦ All Weekly Elite benefits included\n"
        "✦ Best value for long-term users\n"
        "\n"
        "💰 <b>Payment Mode:</b> UPI Only\n"
        "</blockquote>"
    )
    buttons = [[{"text": "💳 BUY VIP PLAN", "callback_data": "buy_vip", "style": "primary"}]]
    await send_raw_api_message(message.chat.id, text, buttons=buttons)

@Client.on_message(filters.command("me") & filters.private)
async def me_cmd(client, message):
    user_id = message.from_user.id
    is_admin = user_id in config.Config.ADMIN_IDS
    
    user = await db.get_user(user_id)
    if not user: return

    status = "VIP Premium" if user.get('is_premium') else "Standard Free"
    time_left = "Unlimited VIP" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    expiry_info = ""
    if user.get('premium_expiry'): 
        expiry_info = f"📅 <b>Expiry date:</b> <code>{user['premium_expiry'].strftime('%Y-%m-%d %H:%M')}</code>\n"

    display_name = config.Config.ADMIN_GOD_NAME if is_admin else f"#{user['nickname']}"

    me_msg = (
        "<blockquote>"
        f"📊 <b>User profile dashboard</b>\n"
        f"\n"
        f"👤 <b>Nickname:</b> <code>{display_name}</code>\n"
        f"🆔 <b>User ID:</b> <code>HIDDEN (ANONYMOUS)</code>\n"
        f"⭐ <b>Account:</b> {status}\n"
        f"\n"
        f"📈 <b>Total media sent:</b> <code>{user.get('total_sent', 0)}</code>\n"
        f"👥 <b>Referral points:</b> <code>{user.get('ref_balance', 0)}</code>\n"
        f"⏳ <b>Active time left:</b> <code>{time_left}</code>\n"
        f"{expiry_info}"
        f"\n"
        f"📩 <b>Join now:</b> <a href='https://t.me/roomjoinus'>@roomjoinus</a>"
        "</blockquote>"
    )
    await message.reply(me_msg, disable_web_page_preview=True)
