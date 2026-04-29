import asyncio
import logging
from datetime import datetime
import pyrogram.utils
from pyrogram import Client, enums
from pyrogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
import aiohttp

import config
from database import db
from SAMRABOTZ_PLUGIN.broadcast import broadcast_worker

logger = logging.getLogger("MAIN")

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
    try:
        app = web.Application()
        app.router.add_get('/', health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', config.Config.PORT)
        await site.start()
        logger.info(f"Web server established on Port {config.Config.PORT}")
    except Exception as e:
        logger.error(f"Web server failed to start: {str(e)}", exc_info=True)

async def ping_server():
    ping_url = f"http://127.0.0.1:{config.Config.PORT}/"
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ping_url) as response:
                    if response.status != 200:
                        logger.warning(f"Ping returned unexpected status: {response.status}")
        except Exception as e:
            logger.error(f"Ping server failed: {str(e)}", exc_info=True)
        await asyncio.sleep(5 * 60)

async def run_2h_reminders():
    try:
        inactive_users = await db.get_users_to_remind()
        reminder_text = (
            "> ⚠️ <b>Attention: Your time has expired</b>\n"
            "> \n"
            "> Please send any media to extend your access.\n"
            "> Each video or image sent grants you an additional <b>30 minutes</b>.\n"
            "> \n"
            "> <i>Your access will be restored immediately upon sending media.</i>"
        )
        for u in inactive_users:
            try:
                await bot.send_message(u['user_id'], reminder_text)
                await db.update_reminded(u['user_id'])
            except Exception as e:
                logger.error(f"Failed to send reminder to {u['user_id']}: {str(e)}", exc_info=True)
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Failed to process reminders: {str(e)}", exc_info=True)

async def expiry_check():
    try:
        await db.remove_expired_premium()
    except Exception as e:
        logger.error(f"Failed to check premium expiry: {str(e)}", exc_info=True)

async def main():
    config.media_queue = asyncio.Queue()
    
    await start_web_server()
    asyncio.create_task(ping_server())
    
    await bot.start()
    restart_text = (
        "> ✅ <b>System restart successful</b>\n"
        "> \n"
        "> <i>All neural networks are online and operational.</i>"
    )
    
    for admin_id in config.Config.ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=restart_text)
        except Exception as e:
            logger.error(f"Failed to alert Admin {admin_id}: {str(e)}", exc_info=True)
            
    try:
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
    except Exception as e:
        logger.error(f"Failed to set bot commands: {str(e)}", exc_info=True)
    
    asyncio.create_task(broadcast_worker(bot))
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_2h_reminders, "interval", minutes=15)
    scheduler.add_job(expiry_check, "interval", minutes=5)
    scheduler.start()
    
    logger.info("Bot Initialization Complete. UI & Systems Online.")
    await pyrogram.idle()
    await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("System Terminated Manually.")
    except Exception as e:
        logger.error(f"Fatal system error: {str(e)}", exc_info=True)
