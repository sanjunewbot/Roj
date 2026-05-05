import logging
from pyrogram import Client, filters
import config
from database import db
from utils import ref_keyboard, send_raw_api_message

logger = logging.getLogger("REFERRAL")

@Client.on_message(filters.command(["referral", "refferal"]) & filters.private)
async def referral_cmd(client, message):
    bot_config = await db.get_bot_settings()
    if not bot_config.get('ref_system'): 
        return await message.reply(
            "<blockquote>"
            "❌ <b>System alert</b>\n"
            "\n"
            "Referral system is currently disabled."
            "</blockquote>"
        )

    user = await db.get_user(message.from_user.id)
    if not user: return

    bot_info = client.me
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    text = (
        "<blockquote>"
        f"👥 <b>Referral network</b>\n"
        f"\n"
        f"{bot_config.get('ref_text', '')}\n"
        f"\n"
        f"🔗 <b>Your exclusive link:</b>\n"
        f"<code>{ref_link}</code>\n"
        f"\n"
        f"🪙 <b>Points:</b> {user['ref_balance']}/{bot_config['ref_count']}"
        "</blockquote>"
    )

    await send_raw_api_message(
        message.from_user.id,
        text,
        buttons=ref_keyboard()
    )

@Client.on_message(filters.command("ref") & filters.user(config.Config.ADMIN_IDS))
async def ref_cmd_init(client, message):
    try:
        if len(message.command) < 2: 
            return await message.reply(
                "<blockquote>"
                "⚙️ <b>Syntax error</b>\n"
                "\n"
                "Use format: <code>/ref on</code> or <code>/ref off</code>"
                "</blockquote>"
            )

        if message.command[1].lower() == "off":
            await db.update_settings({"ref_system": False})
            return await message.reply(
                "<blockquote>"
                "✅ <b>Referral system offline</b>\n"
                "\n"
                "Protocol successfully disabled."
                "</blockquote>"
            )

        config.admin_states[message.from_user.id] = {"step": "ref_1"}
        await message.reply(
            "<blockquote>"
            "🔢 <b>Initiating setup</b>\n"
            "\n"
            "Enter the required number of referrals for a reward."
            "</blockquote>"
        )
    except Exception as e:
        logger.error(f"Referral admin command failed: {str(e)}", exc_info=True)
        await message.reply(
            "<blockquote>"
            f"❌ <b>System fault</b>\n"
            "\n"
            f"An error occurred: {e}"
            "</blockquote>"
        )
