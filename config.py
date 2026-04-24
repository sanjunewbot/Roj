import os, time, asyncio
class Config:
    API_ID = int(os.environ.get("API_ID", "22135296"))  
    API_HASH = os.environ.get("API_HASH", "b3051c4c2dfe4ef65f7146d172d3ddaf")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8660092184:AAEBYIU6lBaVvS8M6MK372UU9qDCExDNYAM")
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://samplesamra:samplesamra@samplesamra.qtff1nr.mongodb.net/?appName=samplesamra")
    ADMIN_IDS = [7893435873]
    FORCE_SUB_CHANNEL = "roomjoinus"
    PORT = int(os.environ.get("PORT", 8080))
    PING_URL = os.environ.get("PING_URL", "http://0.0.0.0:8080")
    MUTE_DURATION_HOURS = 12
START_TIME = time.time()
media_queue = asyncio.Queue()
album_cache = {} 
admin_states = {} 
START_TEXT_TEMPLATE = ("🚀 <b>Welcome to Anonymous Media Exchange!</b>\n\nShare media and it will be forwarded to all users anonymously!\nEach media gives you 30 min (max 24 hours).\n\n👤 <b>Your anonymous name:</b> {name}\n⏳ <b>Time remaining:</b> {time}\n\n🛠 <b>Available Commands:</b>\n• /start - Show this dashboard\n• /register [name] - Change your name\n• /me - Check detailed stats\n• /referral - Get your invite link\n• /join - VIP benefits")
RULES_TEXT = ("📜 <b>Bot Rules:</b>\n\nKeep your focus on sending leaks, candids, snapgod, teens, Ragnar stuff, rough and hardcore stuff. Send whatever content you would love to receive.\n\n⚠️ <b>STRICT RULES:</b>\nThere is a rule in this room\nNo offensive talk\n𝗽𝗲𝗱𝗼𝗽𝗵𝗶𝗹𝗶𝗮\n𝗦𝗰𝗮𝗺𝗺𝗲𝗿\n𝗢𝗯𝘀𝗰𝗲𝗻𝗲 𝗯𝗲𝗵𝗮𝘃𝗶𝗼𝗿\n𝗶𝗻𝗰𝗲𝘀𝘁\nNo promotions\nNo CP\nNo animal porn\nNo dick pics\n\n🚨 <b>Reward for breaking rules: BANNED.</b>")
JOIN_TEXT = ("💎 <b>VIP vs FREE Plans</b>\n\n🆓 <b>Free Plan</b>\n• 30 sec delay for media delivery.\n• Normal queue (no priority).\n• Stay active: 1 media batch = 30 min active time (max 24h).\n\n👑 <b>VIP Plan</b>\n• Unlimited access – only 10 sec delay.\n• No need to stay online or share.\n• Priority speed.\n• VIP Group & Mega Folder Available: 100k+ all types content.\n\n💰 <b>Upgrade Options:</b>\n• Telegram Stars, Crypto (BTC/XMR), Giftcards.\nContact Admin to upgrade.⚠️ If you are restricted, kindly text our support bot: ")
