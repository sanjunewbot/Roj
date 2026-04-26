import os
import time

class Config:
    API_ID = int(os.environ.get("API_ID", "22135296"))
    API_HASH = os.environ.get("API_HASH", "b3051c4c2dfe4ef65f7146d172d3ddaf")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8660092184:AAEBYIU6lBaVvS8M6MK372UU9qDCExDNYAM")
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://samplesamra:samplesamra@samplesamra.qtff1nr.mongodb.net/?appName=samplesamra")
    
    ADMIN_IDS = [7893435873]
    FORCE_SUB_CHANNEL = "-1003843949677"
    
    PORT = int(os.environ.get("PORT", 8080))
    PING_URL = os.environ.get("PING_URL", "http://0.0.0.0:8080")
    
    MUTE_DURATION_HOURS = 12
    MUTE_PENALTY_MINUTES = 2

START_TIME = time.time()
# The queue will be initialized safely in main.py to avoid asyncio loop errors
media_queue = None
album_cache = {}
admin_states = {}

START_TEXT_TEMPLATE = (
    "🚀 <b>Welcome to the Anonymous Media Exchange!</b>\n\n"
    "Your gateway to high-speed anonymous media sharing.\n\n"
    "👤 <b>Your Identity:</b> {name}\n"
    "⏳ <b>Access Time:</b> {time}\n"
    "⭐ <b>Plan:</b> {status}\n\n"
    "🛠 <b>Quick Commands:</b>\n"
    "• /me - Full Profile Details\n"
    "• /referral - Earn VIP Access\n"
    "• /help - All Commands List"
)

ME_TEXT_TEMPLATE = (
    "📊 <b>USER PROFILE DASHBOARD</b>\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "👤 <b>Nickname:</b> <code>#{name}</code>\n"
    "🆔 <b>User ID:</b> <code>{user_id}</code>\n"
    "⭐ <b>Account:</b> {status}\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "📈 <b>Total Media Sent:</b> <code>{total_sent}</code>\n"
    "👥 <b>Referral Points:</b> <code>{ref_bal}</code>\n"
    "⏳ <b>Active Time Left:</b> <code>{time_left}</code>\n"
    "{expiry_info}"
    "━━━━━━━━━━━━━━━━━━\n"
    "<i>Tip: Send media to increase your time!</i>"
)

RULES_TEXT = (
    "📜 <b>Bot Rules & Guidelines:</b>\n\n"
    "Share high-quality content you would love to receive. Keep the media flowing.\n\n"
    "⚠️ <b>STRICTLY PROHIBITED:</b>\n"
    "• No offensive language or harassment\n"
    "• No pedophilia or child abuse material (CP)\n"
    "• No scamming or unauthorized promotions\n"
    "• No obscene behavior or incest\n"
    "• No animal pornography\n"
    "• No unsolicited pictures of genitalia\n\n"
    "🚨 <b>Penalty for violation: PERMANENT BAN.</b>"
)

JOIN_TEXT = (
    "💎 <b>VIP Premium vs FREE Tier</b>\n\n"
    "🆓 <b>Free Tier</b>\n"
    "• 30-second delay for media delivery.\n"
    "• Standard queue priority.\n"
    "• Activity required: 1 media batch = 30 minutes of access (max 24h).\n\n"
    "👑 <b>VIP Premium Tier</b>\n"
    "• Unlimited, unconditional access.\n"
    "• Zero-delay priority delivery (10 seconds).\n"
    "• No requirement to share media to stay active.\n"
    "• Access to the Exclusive VIP Group & Mega Folder (100k+ files).\n\n"
    "💰 <b>Upgrade Options:</b>\n"
    "• Telegram Stars, Crypto (BTC/XMR), or Giftcards.\n"
    "Contact an Administrator to upgrade. If you are restricted, text our support."
)
