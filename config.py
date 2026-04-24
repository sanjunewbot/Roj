# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
import os
import time
import asyncio
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
class Config:
    API_ID = int(os.environ.get("API_ID", ""))  
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://a:a@loude.0uy8em5.mongodb.net/?appName=LOUDE")
    ADMIN_IDS = [7893435873, 8002345109]
    FORCE_SUB_CHANNEL = "" #WHITOUT @
    # ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
    # Deployment Settings (For Koyeb/Heroku)
    PORT = int(os.environ.get("PORT", 8080))
    PING_URL = os.environ.get("PING_URL", "http://0.0.0.0:8080")

# Shared Globals
START_TIME = time.time()
media_queue = asyncio.Queue()
album_cache = {} 
admin_states = {} 

# Original Texts from Raw Code Restored
START_TEXT_TEMPLATE = (
    "🚀 <b>Welcome to Anonymous Media Exchange!</b>\n\n"
    "Share media and it will be forwarded to all users anonymously!\n"
    "Each media gives you 30 min (max 24 hours).\n\n"
    "👤 <b>Your anonymous name:</b> {name}\n"
    "⏳ <b>Time remaining:</b> {time}\n\n"
    "🛠 <b>Available Commands:</b>\n"
    "• /start - Show this dashboard\n"
    "• /register [name] - Change your name\n"
    "• /me - Check detailed stats\n"
    "• /referral - Get your invite link\n"
    "• /join - VIP benefits"
)
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
RULES_TEXT = (
    "📜 <b>Bot Rules:</b>\n\n"
    "Keep your focus on sending leaks, candids, snapgod, teens, Ragnar stuff, rough and hardcore stuff. "
    "Send whatever content you would love to receive.\n\n"
    "⚠️ Don't send any random pics or screenshots otherwise medal for Good content awaits for you (Ban)."
)

# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------

JOIN_TEXT = (
    "💎 <b>VIP vs FREE Plans</b>\n\n"
    "🆓 <b>Free Plan</b>\n"
    "• 30 sec delay for media delivery.\n"
    "• Normal queue (no priority).\n"
    "• Stay active: 1 media batch = 30 min active time (max 24h).\n\n"
    "👑 <b>VIP Plan</b>\n"
    "• Unlimited access – only 10 sec delay.\n"
    "• No need to stay online or share.\n"
    "• Priority speed.\n"
    "• VIP Group: 200k+ content.\n\n"
    "💰 <b>Upgrade Options:</b>\n"
    "• Telegram Stars, Crypto (BTC/XMR), Giftcards.\n"
    "Contact Admin to upgrade."
)
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------