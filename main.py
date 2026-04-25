import asyncio
from datetime import datetime
import pyrogram.utils
from pyrogram import Client, enums
from pyrogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

from config import Config
from database import db
from SAMRABOTZ_PLUGIN.broadcast import broadcast_worker 

pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -1009999999999

bot = Client(
    "SAMRABOTZ", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN, 
    parse_mode=enums.ParseMode.HTML, 
    plugins=dict(root="SAMRABOTZ_PLUGIN")
)

async def health_check(request):
    return web.Response(text="System is Online and Operational.")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', Config.PORT)
    await site.start()
    print(f"🌐 Web server established on Port {Config.PORT}")

async def ping_server():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(Config.PING_URL) as response:
                    pass
        except:
            pass
        await asyncio.sleep(5 * 60)

async def run_2h_reminders():
    inactive_users = await db.get_users_to_remind()
    reminder_text = (
        "⚠️ <b>ATTENTION: YOUR TIME HAS EXPIRED!</b>\n\n"
        "Please send any media to extend your access. Each video or image sent grants you an additional <b>30 minutes</b>.\n\n"
        "Your access will be restored immediately upon sending media! 🚀"
    )
    for u in inactive_users:
        try:
            await bot.send_message(u['user_id'], reminder_text)
            await db.update_reminded(u['user_id'])
        except:
            pass
        await asyncio.sleep(0.1)

async def expiry_check():
    await db.remove_expired_premium()

async def main():
    await start_web_server()
    asyncio.create_task(ping_server())
    
    await bot.start()
    restart_text = "✅ <b>System Restart Successful. All neural networks are online.</b>"
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=restart_text)
        except Exception as e:
            print(f"Failed to alert Admin {admin_id}: {e}")
            
    await bot.set_bot_commands([
        BotCommand("start", "🚀 Access Anonymous Dashboard"),
        BotCommand("register", "🎭 Modify Cyber Identity"),
        BotCommand("me", "📊 View Profile & Status"),
        BotCommand("referral", "👥 Refer Network & Get Premium"),
        BotCommand("join", "💎 View Exclusive VIP Perks"),
        BotCommand("help", "❓ Show Command Directory"),
        BotCommand("add", "🎁 Admin: Grant Premium (#Nickname)"),
        BotCommand("rem_prem", "✂️ Admin: Revoke Premium (#Nickname)"),
        BotCommand("mute", "🔇 Admin: Restrict User"),
        BotCommand("unmute", "🔊 Admin: Remove Restriction"),
        BotCommand("ban", "🔨 Admin: Ban Violator"),
        BotCommand("unban", "🕊️ Admin: Pardon User"),
        BotCommand("restrict", "🔒 Admin: Content Protection"),
        BotCommand("binch", "🗑️ Admin: Assign Backup Core"),
        BotCommand("pmdlt", "⏱️ Admin: Configure Auto-Purge"),
        BotCommand("ref", "⚙️ Admin: Setup Referral Logic"),
        BotCommand("stats", "📈 Admin: System Diagnostics"),
        BotCommand("wait", "🚦 Admin: Registration Lock"),
        BotCommand("broadcast", "📢 Admin: Global Transmission"),
        BotCommand("chat", "💬 Admin: Global Chat Protocol")
    ])
    
    asyncio.create_task(broadcast_worker(bot))
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_2h_reminders, "interval", minutes=15) 
    scheduler.add_job(expiry_check, "interval", minutes=5)
    scheduler.start()
    
    print("🚀 Bot Initialization Complete. UI & Systems Online.")
    await pyrogram.idle()
    await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print("🛑 System Terminated Manually.")
