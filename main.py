import asyncio
from datetime import datetime
import pyrogram.utils
from pyrogram import Client, enums
from pyrogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
from config import Config
from database import db
# Updated Path for your new folder name
from SAMRABOTZ_PLUGIN.broadcast import broadcast_worker 

pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -1009999999999

# Root plugins dictionary updated to SAMRABOTZ_PLUGIN
bot = Client("SAMRABOTZ", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN, parse_mode=enums.ParseMode.HTML, plugins=dict(root="SAMRABOTZ_PLUGIN"))

# ☁️ Web Server for Koyeb/Heroku Health Checks
async def health_check(request):
    return web.Response(text="Bot is ALIVE and RUNNING!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
    await site.start()
    print(f"🌐 Web server running on Port {Config.PORT}")

# 🔄 Self-Ping (Anti-Sleep)
async def ping_server():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(Config.PING_URL) as response:
                    pass
        except: pass
        await asyncio.sleep(5 * 60)

# 🔔 2-Hour Reminder System
async def run_2h_reminders():
    inactive_users = await db.get_users_to_remind()
    for u in inactive_users:
        try:
            await bot.send_message(u['user_id'], "⚠️ <b>Time's Up!</b>\n\nYour active time is 0 mins. You will not receive any media. Share 1 media to get 30 mins time!")
            await db.update_reminded(u['user_id'])
        except: pass
        await asyncio.sleep(0.1)
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
async def expiry_check(): 
    await db.remove_expired_premium()

async def main():
    await start_web_server()
    asyncio.create_task(ping_server())
    
    await bot.start()
    
    # 🚀 RESTART NOTIFICATION TO ADMINS
    restart_text = (
        "✅ <b>Bot Restarted!</b>"
    )
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=restart_text)
        except Exception as e:
            print(f"Could not send restart alert to Admin {admin_id}: {e}")
            pass
            
    # 🔥 STYLISH AUTO-SET MENU COMMANDS (Single List for Users & Admins)
    await bot.set_bot_commands([
        BotCommand("start", "🚀 Start Anonymous Dashboard"),
        BotCommand("register", "🎭 Change Your Ghost Name"),
        BotCommand("me", "📊 Check Profile & Premium Status"),
        BotCommand("referral", "👥 Refer Friends & Get Premium"),
        BotCommand("join", "💎 Explore Exclusive VIP Benefits"),
        BotCommand("help", "❓ Show Full Command Menu"),
        BotCommand("rem_prem", "✂️ Admin: Remove User Premium"),
        BotCommand("restrict", "🔒 Admin: Toggle Media Restriction"),
        BotCommand("binch", "🗑️ Admin: Set Backup Bin Channel"),
        BotCommand("pmdlt", "⏱️ Admin: Configure Auto-Delete"),
        BotCommand("add", "🎁 Admin: Grant Manual Premium"),
        BotCommand("ref", "⚙️ Admin: Setup Referral System"),
        BotCommand("ban", "🔨 Admin: Ban Abusive User"),
        BotCommand("unban", "🕊️ Admin: Unban Restricted User"),
        BotCommand("stats", "📈 Admin: View Live Bot Statistics"),
        BotCommand("wait", "🚦 Admin: Toggle New Registrations"),
        BotCommand("broadcast", "📢 Admin: Mass Message Broadcast")
    ])
    
    asyncio.create_task(broadcast_worker(bot))
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_2h_reminders, "interval", minutes=15) 
    scheduler.add_job(expiry_check, "interval", minutes=5)
    scheduler.start()
    
    print("🚀 Bot Started! Stylish Auto-Set Menu & Restart Alerts Loaded.")
    await asyncio.Event().wait()
# ---------------------------------------------------------
# 🤖 PROJECT: SAMRABOTZ ANONYMOUS MEDIA
# ---------------------------------------------------------
# 👑 DEVELOPER : @SHEFFYSAMRA1
# 📢 CHANNEL   : @SAMRABOTZ
# ---------------------------------------------------------
# Please do not remove these credits. Respect the hard work!
# ---------------------------------------------------------
if __name__ == "__main__":
    bot.run(main())