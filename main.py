import asyncio
from datetime import datetime
import pyrogram.utils
from pyrogram import Client, enums
from pyrogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

import config
from database import db
from SAMRABOTZ_PLUGIN.broadcast import broadcast_worker

pyrogram.utils.MIN_CHAT_ID = -999999999999
pyrogram.utils.MIN_CHANNEL_ID = -1009999999999

bot = Client(
    "SAMRABOTZ",
    api_id=config.Config.API_ID,
    api_hash=config.Config.API_HASH,
    bot_token=config.Config.BOT_TOKEN,
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
    site = web.TCPSite(runner, '0.0.0.0', config.Config.PORT)
    await site.start()
    print(f"🌐 Web server established on Port {config.Config.PORT}")

async def ping_server():
    import aiohttp
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config.Config.PING_URL) as response:
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
    config.media_queue = asyncio.Queue()
    
    await start_web_server()
    asyncio.create_task(ping_server())
    
    await bot.start()
    restart_text = "✅ <b>System Restart Successful. All neural networks are online.</b>"
    
    for admin_id in config.Config.ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=restart_text)
        except Exception as e:
            print(f"Failed to alert Admin {admin_id}: {e}")
            
    await bot.set_bot_commands([
        BotCommand("start", "🚀 DASHBOARD & STATUS"),
        BotCommand("register", "🎭 UPDATE IDENTITY"),
        BotCommand("me", "📊 DETAILED PROFILE STATS"),
        BotCommand("referral", "👥 EARN VIP ACCESS"),
        BotCommand("plans", "💎 VIEW PLANS & BENEFITS"),
        BotCommand("help", "❓ OPEN COMMAND MENU"),
        BotCommand("add", "🎁 ADMIN: GRANT PREMIUM"),
        BotCommand("rem_prem", "✂️ ADMIN: REMOVE PREMIUM"),
        BotCommand("mute", "🔇 ADMIN: MUTE USER"),
        BotCommand("unmute", "🔊 ADMIN: UNMUTE USER"),
        BotCommand("ban", "🔨 ADMIN: BAN USER"),
        BotCommand("unban", "🕊️ ADMIN: UNBAN USER"),
        BotCommand("restrict", "🔒 ADMIN: PROTECTION MODE"),
        BotCommand("binch", "🗑️ ADMIN: SET BACKUP BIN"),
        BotCommand("pmdlt", "⏱️ ADMIN: AUTO PURGE SETUP"),
        BotCommand("ref", "⚙️ ADMIN: REFERRAL CONFIG"),
        BotCommand("get_buttn", "🎥 ADMIN: MEDIA HISTORY"),
        BotCommand("stats", "📈 ADMIN: LIVE SYSTEM DIAGNOSTICS"),
        BotCommand("wait", "🚦 ADMIN: REGISTRATION LOCK"),
        BotCommand("broadcast", "📢 ADMIN: GLOBAL MESSAGE"),
        BotCommand("chat", "💬 ADMIN: GLOBAL CHAT TOGGLE")
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
