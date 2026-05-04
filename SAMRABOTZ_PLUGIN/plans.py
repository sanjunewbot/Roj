from pyrogram import Client, filters
from datetime import datetime
import config
from database import db
from utils import get_time_left

@Client.on_message(filters.command("plans") & filters.private)
async def plans_cmd(client, message):
    text = (
        "<blockquote>"
        "💎 <b>VIP premium vs standard free</b>
"
        "
"
        "❖ <b>Standard Free Tier</b> ❖
"
        "✦ 30-second delay for media delivery
"
        "✦ Standard queue priority
"
        "✦ Activity required: 1 Media Batch = 30 Minutes Access (Max 24H)
"
        "
"
        "👑 <b>VIP Premium Tier</b> 👑
"
        "✦ Unlimited, unconditional access
"
        "✦ Zero-delay priority delivery (≈10 seconds)
"
        "✦ No need to share media to stay active
"
        "✦ Access to exclusive VIP group & mega folder (100K+ files)
"
        "
"
        "💰 <b>Payment mode:</b> UPI Only
"
        "📩 <b>Join now:</b> <a href='https://t.me/roomjoinus'>@roomjoinus</a>"
        "</blockquote>"
    )
    await message.reply(text, disable_web_page_preview=True)

@Client.on_message(filters.command("me") & filters.private)
async def me_cmd(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user: return

    status = "VIP Premium" if user.get('is_premium') else "Standard Free"
    time_left = "Unlimited VIP" if user.get('is_premium') else get_time_left(user.get('active_until', datetime.now()))
    expiry_info = ""
    if user.get('premium_expiry'): 
        expiry_info = f"> 📅 <b>Expiry date:</b> <code>{user['premium_expiry'].strftime('%Y-%m-%d %H:%M')}</code>
"

    me_msg = (
        "<blockquote>"
        f"📊 <b>User profile dashboard</b>
"
        f"
"
        f"👤 <b>Nickname:</b> <code>#{user['nickname']}</code>
"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>
"
        f"⭐ <b>Account:</b> {status}
"
        f"
"
        f"📈 <b>Total media sent:</b> <code>{user.get('total_sent', 0)}</code>
"
        f"👥 <b>Referral points:</b> <code>{user.get('ref_balance', 0)}</code>
"
        f"⏳ <b>Active time left:</b> <code>{time_left}</code>
"
        f"{expiry_info}"
        f"
"
        f"📩 <b>Join now:</b> <a href='https://t.me/roomjoinus'>@roomjoinus</a>"
        "</blockquote>"
    )
    await message.reply(me_msg, disable_web_page_preview=True)
