import os
import time
import asyncio

class Config:
    API_ID = int(os.environ.get("API_ID", "22135296"))  
    API_HASH = os.environ.get("API_HASH", "b3051c4c2dfe4ef65f7146d172d3ddaf")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8660092184:AAEBYIU6lBaVvS8M6MK372UU9qDCExDNYAM")
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://samplesamra:samplesamra@samplesamra.qtff1nr.mongodb.net/?appName=samplesamra")
    
    ADMIN_IDS = [7893435873]
    # You can put a channel ID (e.g., -100123456789) or username (e.g., roomjoinus or @roomjoinus)
    FORCE_SUB_CHANNEL = "roomjoinus" 
    
    PORT = int(os.environ.get("PORT", 8080))
    PING_URL = os.environ.get("PING_URL", "http://0.0.0.0:8080")
    
    MUTE_DURATION_HOURS = 12
    MUTE_PENALTY_MINUTES = 2

START_TIME = time.time()
media_queue = asyncio.Queue()
album_cache = {} 
admin_states = {} 

START_TEXT_TEMPLATE = (
    "🚀 <b>Welcome to the Anonymous Media Exchange!</b>\n\n"
    "Share media and it will be forwarded to all active users anonymously!\n"
    "Each media sent grants you an additional 30 minutes (maximum 24 hours).\n\n"
    "👤 <b>Your Anonymous Identity:</b> {name}\n"
    "⏳ <b>Time Remaining:</b> {time}\n\n"
    "🛠 <b>Available Commands:</b>\n"
    "• /start - Show this dashboard\n"
    "• /register [name] - Change your identity\n"
    "• /me - Check detailed statistics\n"
    "• /referral - Get your invite link\n"
    "• /join - View VIP benefits"
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
