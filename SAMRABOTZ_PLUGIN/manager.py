import re
import aiohttp
import logging
import asyncio
import time
from datetime import datetime
from pyrogram import Client, filters
import config
from database import db, users
from utils import get_uptime, parse_duration, edit_raw_api_message, send_raw_api_media, send_raw_api_message

logger = logging.getLogger("MANAGER")

async def aio_reply(chat_id, text, reply_to=None, buttons=None):
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_to: payload["reply_to_message_id"] = reply_to
    if buttons: payload["reply_markup"] = {"inline_keyboard": buttons}
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 429:
                        r = await resp.json()
                        await asyncio.sleep(r.get("parameters", {}).get("retry_after", 3))
                        continue
                    if resp.status != 200:
                        logger.error(f"API send error: {await resp.text()}")
                    return await resp.json()
            except Exception as e:
                logger.error(f"Network error in aio_reply: {e}", exc_info=True)
                return None

async def broadcast_warning(target_nick, action, admin_id, reason):
    if admin_id in config.Config.ADMIN_IDS:
        admin_nick = config.Config.ADMIN_GOD_NAME
    else:
        admin_user = await db.get_user(admin_id)
        admin_nick = f"#{admin_user['nickname']}" if admin_user else "System command"
    
    text = (
        "<blockquote>"
        "🚨 <b>𝔾𝕃𝕆𝔹𝔸𝕃 𝕊𝔼ℂ𝕌ℝ𝕀𝕋𝕐 𝔸𝕃𝔼ℝ𝕋</b>\n"
        "\n"
        f"👤 <b>Target user:</b> #{target_nick}\n"
        f"🔨 <b>Punishment:</b> {action}\n"
        f"👮‍♂️ <b>Action by:</b> {admin_nick}\n"
        f"📝 <b>Reason:</b> {reason}"
        "</blockquote>"
    )
    all_users = await db.get_active_users()
    for u in all_users:
        await aio_reply(u['user_id'], text)
        await asyncio.sleep(0.05)

@Client.on_callback_query(filters.regex(r"^buy_vip$"))
async def buy_vip_preview(client, query):
    text = (
        "<blockquote>"
        "⚠️ <b>Confirm your request</b>\n"
        "\n"
        f"The following message will be sent to <b>{config.Config.ADMIN_GOD_NAME}</b> in the global chat:\n"
        "\n"
        "<i>\"I want to upgrade my account to VIP Premium. Please provide the UPI details for payment.\"</i>"
        "</blockquote>"
    )
    buttons = [
        [{"text": "✅ Send Request", "callback_data": "confirm_buy_vip", "style": "success"}],
        [{"text": "❌ Cancel", "callback_data": "cancel_action", "style": "danger"}]
    ]
    await edit_raw_api_message(query.message.chat.id, query.message.id, text, buttons)

@Client.on_callback_query(filters.regex(r"^confirm_buy_vip$"))
async def confirm_buy_vip(client, query):
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    if not user: return

    bot_config = await db.get_bot_settings()
    upi_id = bot_config.get("upi_id", "Not Configured")
    qr_file_id = bot_config.get("qr_file_id")

    config.pending_payments[user_id] = time.time()

    payment_text = (
        "<blockquote>"
        "💳 <b>VIP purchase initiated</b>\n"
        "\n"
        "Please make the payment using the details below:\n"
        f"<b>UPI ID:</b> <code>{upi_id}</code>\n"
        "\n"
        "<i>⚠️ Send the payment screenshot (Image) here within 5 minutes. Do not send text or links.</i>"
        "</blockquote>"
    )
    
    try:
        await query.message.delete()
    except:
        pass

    if qr_file_id:
        await send_raw_api_media(query.message.chat.id, qr_file_id, "photo", caption=payment_text)
    else:
        await aio_reply(query.message.chat.id, payment_text)

    display_name = f"#{user['nickname'].upper()}"
    chat_text = (
        f"💬 <b>{display_name}</b> ➦ <b>{config.Config.ADMIN_GOD_NAME}</b>\n\n"
        f"💳 I want to upgrade my account to VIP Premium. Please provide the UPI details for payment."
    )
    all_users = await db.get_all_users()
    for target in all_users:
        if target['user_id'] == user_id or target.get('is_banned') or (target.get('chat_muted_until') and target['chat_muted_until'] > datetime.now()):
            continue
        await aio_reply(target['user_id'], chat_text)
        await asyncio.sleep(0.05)

@Client.on_callback_query(filters.regex(r"^revoke_(.+)"))
async def revoke_payment(client, query):
    if query.from_user.id not in config.Config.ADMIN_IDS: return
    nick = query.matches[0].group(1)
    u = await db.get_user_by_nickname(nick)
    if u:
        await aio_reply(
            u['user_id'],
            "<blockquote>"
            "🚨 <b>Payment Verification Failed:</b> Your VIP upgrade request was declined. Reason: Invalid/Fake screenshot or payment not received."
            "</blockquote>"
        )
    try:
        await query.answer("Request Revoked", show_alert=True)
    except: pass
    await edit_raw_api_message(query.message.chat.id, query.message.id, "<blockquote>❌ <b>Request Revoked by Admin</b></blockquote>")

@Client.on_callback_query(filters.regex(r"^addprem_(.+)"))
async def add_prem_payment(client, query):
    if query.from_user.id not in config.Config.ADMIN_IDS: return
    nick = query.matches[0].group(1)
    config.admin_states[query.from_user.id] = {"step": "addprem_custom", "target_nick": nick}
    await aio_reply(
        query.message.chat.id,
        "<blockquote>"
        f"⏳ <b>Adding Premium to #{nick}</b>\n"
        "Please type the duration (e.g., 7d, 30d, 1M, 1y):"
        "</blockquote>"
    )
    try:
        await query.answer("Enter duration in chat.")
    except: pass

@Client.on_callback_query(filters.regex(r"^cancel_action$"))
async def cancel_action(client, query):
    user_id = query.from_user.id
    if user_id in config.admin_states:
        config.admin_states.pop(user_id, None)
    if user_id in config.pending_payments:
        del config.pending_payments[user_id]
    url = f"https://api.telegram.org/bot{config.Config.BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": query.message.chat.id,
        "message_id": query.message.id,
        "text": "<blockquote>✅ <b>Workflow cancelled securely.</b></blockquote>",
        "parse_mode": "HTML"
    }
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, json=payload)
        except Exception as e:
            logger.error(f"Failed to edit message on cancel: {e}", exc_info=True)
    try:
        await query.answer("Action aborted successfully.", show_alert=True)
    except Exception as e:
        logger.warning(f"Failed to answer cancel callback: {e}")

@Client.on_message(filters.command("cancel") & filters.user(config.Config.ADMIN_IDS))
async def cancel_cmd(client, message):
    user_id = message.from_user.id
    if user_id in config.admin_states:
        config.admin_states.pop(user_id, None)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            "✅ <b>Current workflow cancelled successfully.</b>"
            "</blockquote>", 
            message.id
        )
    else:
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            "ℹ️ <b>No active workflow to cancel.</b>"
            "</blockquote>", 
            message.id
        )

@Client.on_message(filters.command("setqr") & filters.user(config.Config.ADMIN_IDS))
async def setqr_cmd(client, message):
    config.admin_states[message.from_user.id] = {"step": "qr_step_1"}
    await aio_reply(
        message.chat.id,
        "<blockquote>"
        "📷 <b>QR setup initiated</b>\n"
        "\n"
        "Please send the QR Code image (Photo) for payments."
        "</blockquote>"
    )

@Client.on_message(filters.command("delqr") & filters.user(config.Config.ADMIN_IDS))
async def delqr_cmd(client, message):
    await db.update_settings({"qr_file_id": None, "upi_id": None})
    await aio_reply(
        message.chat.id,
        "<blockquote>"
        "🗑️ <b>QR removed</b>\n"
        "\n"
        "Payment QR and UPI details have been deleted successfully."
        "</blockquote>"
    )

@Client.on_callback_query(filters.regex(r"^report_(.+)"))
async def handle_report(client, query):
    user_id = query.from_user.id
    if user_id not in config.Config.ADMIN_IDS:
        try:
            return await query.answer("🚨 Only administrators can use the report function.", show_alert=True)
        except Exception as e:
            logger.warning(f"Failed to answer report callback for non-admin: {e}")
            return

    target_nick = query.matches[0].group(1)
    try:
        await query.answer("Report initiated.")
    except Exception as e:
        logger.warning(f"Failed to answer report callback: {e}")

    config.admin_states[user_id] = {"step": "mute_1", "target_nick": target_nick}
    buttons = [[{"text": "Cancel Report", "callback_data": "cancel_action", "style": "danger"}]]
    await aio_reply(
        user_id, 
        "<blockquote>"
        f"🚨 <b>Report workflow activated for #{target_nick}</b>\n"
        "\n"
        "📝 Please reply with the number of days to mute this user (e.g., <code>1</code> for 1 day)."
        "</blockquote>",
        buttons=buttons
    )

@Client.on_message(filters.command("stats") & filters.user(config.Config.ADMIN_IDS))
async def stats_cmd(client, message):
    try:
        t, a, b = await db.get_stats()
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"📈 <b>System diagnostics</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Total identities:</b> <code>{t}</code>\n"
            f"🟢 <b>Active nodes:</b> <code>{a}</code>\n"
            f"🔴 <b>Banished entities:</b> <code>{b}</code>\n"
            f"⏱ <b>Core uptime:</b> <code>{get_uptime()}</code>\n"
            f"━━━━━━━━━━━━━━━━━━"
            "</blockquote>", 
            message.id
        )
    except Exception as e: 
        logger.error(f"Stats command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("add") & filters.user(config.Config.ADMIN_IDS))
async def manual_add(client, message):
    try:
        if len(message.command) < 3: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "🎁 <b>Syntax:</b> <code>/add #Nickname 30d</code>"
                "</blockquote>", 
                message.id
            )
        nick = message.command[1].replace("#", "")
        dur = parse_duration(message.command[2])
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                f"❌ <b>Error:</b> Identity #{nick} does not exist."
                "</blockquote>", 
                message.id
            )
        if dur:
            await users.update_one({"user_id": u['user_id']}, {"$set": {"is_premium": True, "premium_expiry": datetime.now() + dur}})
            await aio_reply(
                message.chat.id, 
                "<blockquote>"
                f"✅ <b>VIP credentials granted:</b> #{nick} for {message.command[2]}"
                "</blockquote>", 
                message.id
            )
            try: 
                await client.send_message(
                    u['user_id'], 
                    "<blockquote>"
                    "💎 <b>VIP premium status acquired!</b> You now have unlimited, zero-delay access."
                    "</blockquote>"
                )
            except Exception as e:
                logger.warning(f"Failed to notify user {u['user_id']} of premium status: {e}")
        else: 
            await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Error:</b> Invalid time parameter (acceptable: 1d, 30m, 1h)."
                "</blockquote>", 
                message.id
            )
    except Exception as e: 
        logger.error(f"Add premium command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("rem_prem") & filters.user(config.Config.ADMIN_IDS))
async def rem_prem_cmd(client, message):
    try:
        if len(message.command) < 2: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "✂️ <b>Syntax:</b> <code>/rem_prem #Nickname</code>"
                "</blockquote>", 
                message.id
            )
        nick = message.command[1].replace("#", "")
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                f"❌ <b>Error:</b> Identity #{nick} does not exist."
                "</blockquote>", 
                message.id
            )
        await db.remove_premium(u['user_id'])
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"✅ <b>VIP credentials revoked:</b> #{nick}"
            "</blockquote>", 
            message.id
        )
        try: 
            await client.send_message(
                u['user_id'], 
                "<blockquote>"
                "⚠️ <b>Warning: Your VIP access has been terminated by command center.</b>"
                "</blockquote>"
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {u['user_id']} of premium removal: {e}")
    except Exception as e: 
        logger.error(f"Remove premium command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("mute") & filters.user(config.Config.ADMIN_IDS))
async def mute_cmd(client, message):
    try:
        nick = None
        args = []
        if len(message.command) > 1 and message.command[1].startswith("#"):
            nick = message.command[1].replace("#", "")
            args = message.command[2:]
        elif message.reply_to_message and (message.reply_to_message.caption or message.reply_to_message.text):
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match: nick = match.group(1).strip()
            args = message.command[1:]
        if not nick: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Error:</b> Reply to a message or use <code>/mute #Nickname</code>."
                "</blockquote>", 
                message.id
            )
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                f"❌ <b>Error:</b> Identity #{nick} not found."
                "</blockquote>", 
                message.id
            )
        if u['user_id'] in config.Config.ADMIN_IDS: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Action denied:</b> Administrators possess system immunity."
                "</blockquote>", 
                message.id
            )
        days, reason = 1, "Violation of network guidelines"
        if len(args) > 0 and args[0].isdigit():
            days = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0: reason = " ".join(args)
        
        await db.mute_user(u['user_id'], days * 24)
        
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"🔇 <b>Target silenced:</b> #{nick}\n"
            f"⏳ <b>Duration:</b> {days} Days\n"
            f"📝 <b>Reason:</b> {reason}"
            "</blockquote>", 
            message.id
        )
        
        action_text = f"Muted for {days} days"
        asyncio.create_task(broadcast_warning(nick, action_text, message.from_user.id, reason))
        
        try: 
            await client.send_message(
                u['user_id'], 
                "<blockquote>"
                f"🔇 <b>System alert: You have been MUTED for {days} days.</b>\n"
                f"📝 <b>Reason:</b> {reason}\n"
                f"<i>Transmitting and receiving media is disabled.</i>"
                "</blockquote>"
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {u['user_id']} of mute: {e}")
    except Exception as e: 
        logger.error(f"Mute command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("unmute") & filters.user(config.Config.ADMIN_IDS))
async def unmute_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"): nick = message.command[1].replace("#", "")
        elif message.reply_to_message:
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match: nick = match.group(1).strip()
        if not nick: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Error:</b> Reply to a message or use <code>/unmute #Nickname</code>."
                "</blockquote>", 
                message.id
            )
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Error:</b> User record not found."
                "</blockquote>", 
                message.id
            )
        await db.unmute_user(u['user_id'])
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"🔊 <b>Silence revoked:</b> #{u['nickname']}"
            "</blockquote>", 
            message.id
        )
        try: 
            await client.send_message(
                u['user_id'], 
                "<blockquote>"
                "🔊 <b>Your account restrictions have been lifted. Welcome back.</b>"
                "</blockquote>"
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {u['user_id']} of unmute: {e}")
    except Exception as e: 
        logger.error(f"Unmute command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("ban") & filters.user(config.Config.ADMIN_IDS))
async def ban_cmd(client, message):
    try:
        nick = None
        args = []
        if len(message.command) > 1 and message.command[1].startswith("#"):
            nick = message.command[1].replace("#", "")
            args = message.command[2:]
        elif message.reply_to_message and (message.reply_to_message.caption or message.reply_to_message.text):
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match: nick = match.group(1).strip()
            args = message.command[1:]
        if not nick: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Error:</b> Reply to a message or use <code>/ban #Nickname</code>."
                "</blockquote>", 
                message.id
            )
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                f"❌ <b>Error:</b> Identity #{nick} not found."
                "</blockquote>", 
                message.id
            )
        if u['user_id'] in config.Config.ADMIN_IDS: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Action denied:</b> Administrators possess system immunity."
                "</blockquote>", 
                message.id
            )
        days, reason = 365, "Severe protocol violation"
        if len(args) > 0 and args[0].isdigit():
            days = int(args[0])
            reason = " ".join(args[1:]) if len(args) > 1 else reason
        elif len(args) > 0: reason = " ".join(args)
        
        await db.ban_user(u['user_id'], days)
        
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"🔨 <b>Target banished:</b> #{nick}\n"
            f"⏳ <b>Duration:</b> {days} Days\n"
            f"📝 <b>Reason:</b> {reason}"
            "</blockquote>", 
            message.id
        )
        
        action_text = f"Banned for {days} days"
        asyncio.create_task(broadcast_warning(nick, action_text, message.from_user.id, reason))
        
        try: 
            await client.send_message(
                u['user_id'], 
                "<blockquote>"
                f"🚨 <b>Critical alert: Your network access has been permanently revoked for {days} days.</b>\n"
                f"📝 <b>Reason:</b> {reason}"
                "</blockquote>"
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {u['user_id']} of ban: {e}")
    except Exception as e: 
        logger.error(f"Ban command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("unban") & filters.user(config.Config.ADMIN_IDS))
async def unban_cmd(client, message):
    try:
        nick = None
        if len(message.command) > 1 and message.command[1].startswith("#"): nick = message.command[1].replace("#", "")
        elif message.reply_to_message:
            content = message.reply_to_message.caption or message.reply_to_message.text
            match = re.search(r"#(?:<b>)?(.*?)(?:</b>)?\n", content)
            if match: nick = match.group(1).strip()
        if not nick: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Error:</b> Reply to a message or use <code>/unban #Nickname</code>."
                "</blockquote>", 
                message.id
            )
        u = await db.get_user_by_nickname(nick)
        if not u: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "❌ <b>Error:</b> User record not found."
                "</blockquote>", 
                message.id
            )
        await db.unban_user(u['user_id'])
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"🕊️ <b>Target pardoned:</b> #{u['nickname']}"
            "</blockquote>", 
            message.id
        )
    except Exception as e: 
        logger.error(f"Unban command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("chat") & filters.user(config.Config.ADMIN_IDS))
async def toggle_chat(client, message):
    try:
        if len(message.command) < 2: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "💬 <b>Syntax:</b> <code>/chat on</code> or <code>/chat off</code>"
                "</blockquote>", 
                message.id
            )
        mode = message.command[1].lower() == "on"
        await db.update_settings({"chat_enabled": mode})
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"💬 <b>Global chat protocol is now:</b> {'ONLINE' if mode else 'OFFLINE'}"
            "</blockquote>", 
            message.id
        )
    except Exception as e: 
        logger.error(f"Chat toggle command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("restrict") & filters.user(config.Config.ADMIN_IDS))
async def restrict_cmd(client, message):
    try:
        if len(message.command) < 2: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "🔒 <b>Syntax:</b> <code>/restrict on</code> or <code>/restrict off</code>"
                "</blockquote>", 
                message.id
            )
        mode = message.command[1].lower() == "on"
        await db.update_settings({"media_restriction": mode})
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"✅ <b>Media forwarding protection:</b> {'ENGAGED' if mode else 'DISENGAGED'}"
            "</blockquote>", 
            message.id
        )
    except Exception as e: 
        logger.error(f"Restrict toggle command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("wait") & filters.user(config.Config.ADMIN_IDS))
async def wait_cmd(client, message):
    try:
        if len(message.command) < 2: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "🚦 <b>Syntax:</b> <code>/wait on</code> (Lock) or <code>/wait off</code> (Open)"
                "</blockquote>", 
                message.id
            )
        mode = message.command[1].lower() == "on"
        await db.update_settings({"registration_open": not mode})
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"✅ <b>Network entry lock:</b> {'ACTIVE' if mode else 'DISABLED'}"
            "</blockquote>", 
            message.id
        )
    except Exception as e: 
        logger.error(f"Wait toggle command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("pmdlt") & filters.user(config.Config.ADMIN_IDS))
async def toggle_dlt(client, message):
    try:
        if len(message.command) < 2: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "⏱️ <b>Syntax:</b> <code>/pmdlt on 60</code> or <code>/pmdlt off</code>"
                "</blockquote>", 
                message.id
            )
        mode = message.command[1].lower() == "on"
        await db.update_settings({"pm_dlt": mode})
        if mode and len(message.command) >= 3: 
            await db.update_settings({"dlt_time": int(message.command[2])})
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"✅ <b>Auto-purge protocol:</b> {'ONLINE' if mode else 'OFFLINE'}"
            "</blockquote>", 
            message.id
        )
    except Exception as e: 
        logger.error(f"Pmdlt toggle command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("get_buttn") & filters.user(config.Config.ADMIN_IDS))
async def toggle_get_buttn(client, message):
    try:
        if len(message.command) < 2: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "🎥 <b>Syntax:</b> <code>/get_buttn on</code> or <code>/get_buttn off</code>"
                "</blockquote>", 
                message.id
            )
        mode = message.command[1].lower() == "on"
        await db.update_settings({"get_btn_enabled": mode})
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"✅ <b>Media history button:</b> {'ONLINE' if mode else 'OFFLINE'}"
            "</blockquote>", 
            message.id
        )
    except Exception as e: 
        logger.error(f"Get button toggle command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message(filters.command("tutorial") & filters.user(config.Config.ADMIN_IDS))
async def manage_tutorial(client, message):
    try:
        if len(message.command) < 2: 
            return await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "🎬 <b>Syntax:</b> <code>/tutorial on</code> or <code>/tutorial off</code>"
                "</blockquote>", 
                message.id
            )
        mode = message.command[1].lower()
        if mode == "off":
            await db.update_settings({"tutorial_link": None})
            await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "✅ <b>Tutorial video disabled.</b> Crystal button hidden."
                "</blockquote>", 
                message.id
            )
        elif mode == "on":
            config.admin_states[message.from_user.id] = {"step": "tut_1"}
            await aio_reply(
                message.chat.id, 
                "<blockquote>"
                "🔗 <b>System waiting:</b> Please send the tutorial video link (URL)."
                "</blockquote>", 
                message.id
            )
    except Exception as e: 
        logger.error(f"Tutorial toggle command failed: {e}", exc_info=True)
        await aio_reply(
            message.chat.id, 
            "<blockquote>"
            f"❌ <b>System fault:</b> {e}"
            "</blockquote>"
        )

@Client.on_message((filters.text | filters.photo) & filters.private & filters.user(config.Config.ADMIN_IDS) & ~filters.command(["start", "help", "rem_prem", "restrict", "pmdlt", "add", "ref", "ban", "unban", "mute", "unmute", "stats", "wait", "broadcast", "plans", "me", "register", "referral", "chat", "get_buttn", "tutorial", "cancel", "setqr", "delqr"]) & ~filters.regex("^(GET MEDIA HISTORY)$"))
async def master_admin_state_handler(client, message):
    uid = message.from_user.id
    if uid not in config.admin_states: return
    state = config.admin_states[uid]

    msg_text = message.text.strip() if message.text else ""

    if state.get("step") == "qr_step_1":
        if not message.photo:
            return await aio_reply(uid, "<blockquote>❌ <b>Invalid input:</b> Please send a valid image (Photo).</blockquote>")
        state["qr_file_id"] = message.photo.file_id
        state["step"] = "qr_step_2"
        await aio_reply(
            uid,
            "<blockquote>"
            "✅ <b>Image received</b>\n"
            "\n"
            "Now, please send the UPI ID (Text) associated with this QR."
            "</blockquote>"
        )
        return

    elif state.get("step") == "qr_step_2":
        if not msg_text:
            return await aio_reply(uid, "<blockquote>❌ <b>Invalid input:</b> Please send valid text.</blockquote>")
        await db.update_settings({"qr_file_id": state["qr_file_id"], "upi_id": msg_text})
        config.admin_states.pop(uid, None)
        await aio_reply(
            uid,
            "<blockquote>"
            "✅ <b>Setup complete</b>\n"
            "\n"
            "Payment QR and UPI details are now live."
            "</blockquote>"
        )
        return

    if state.get("step") == "mute_1":
        if not msg_text: return
        try:
            days = int(msg_text)
            state["days"] = days
            state["step"] = "mute_2"
            buttons = [[{"text": "Cancel Report", "callback_data": "cancel_action", "style": "danger"}]]
            await aio_reply(
                uid, 
                "<blockquote>"
                f"📝 <b>Provide the reason for muting #{state['target_nick']}:</b>"
                "</blockquote>",
                buttons=buttons
            )
        except ValueError:
            await aio_reply(
                uid, 
                "<blockquote>"
                "❌ <b>Invalid input:</b> Please provide a numeric value for days."
                "</blockquote>"
            )

    elif state.get("step") == "mute_2":
        if not msg_text: return
        reason = msg_text
        nick = state["target_nick"]
        days = state["days"]

        u = await db.get_user_by_nickname(nick)
        if not u:
            await aio_reply(
                uid, 
                "<blockquote>"
                f"❌ <b>Error:</b> Identity #{nick} not found in database."
                "</blockquote>"
            )
        else:
            target_id = u['user_id']
            await db.mute_user(target_id, days * 24)
            logger.info(f"User #{nick} muted by Admin {uid} for {days} days. Reason: {reason}")
            await aio_reply(
                uid, 
                "<blockquote>"
                f"✅ <b>Target silenced:</b> #{nick}\n"
                f"⏳ <b>Duration:</b> {days} Days\n"
                f"📝 <b>Reason:</b> {reason}"
                "</blockquote>"
            )
            
            action_text = f"Muted for {days} days"
            asyncio.create_task(broadcast_warning(nick, action_text, uid, reason))
            
            try: 
                await client.send_message(
                    target_id, 
                    "<blockquote>"
                    f"🔇 <b>System alert: You have been MUTED for {days} days.</b>\n"
                    f"📝 <b>Reason:</b> {reason}\n"
                    f"<i>Transmitting and receiving media is disabled.</i>"
                    "</blockquote>"
                )
            except Exception as e:
                logger.warning(f"Failed to notify user {target_id} of mute via state handler: {e}")
        config.admin_states.pop(uid, None)

    elif state.get("step") == "addprem_custom":
        if not msg_text: return
        dur_str = msg_text
        nick = state["target_nick"]
        dur = parse_duration(dur_str)
        if not dur:
            await aio_reply(uid, "<blockquote>❌ <b>Invalid duration format. Cancelled.</b></blockquote>")
        else:
            u = await db.get_user_by_nickname(nick)
            if u:
                await users.update_one({"user_id": u['user_id']}, {"$set": {"is_premium": True, "premium_expiry": datetime.now() + dur}})
                await aio_reply(uid, f"<blockquote>✅ <b>Premium added to #{nick} for {dur_str}</b></blockquote>")
                try:
                    await client.send_message(
                        u['user_id'],
                        "<blockquote>💎 <b>VIP Premium Activated successfully!</b></blockquote>"
                    )
                except: pass
            else:
                await aio_reply(uid, "<blockquote>❌ <b>User not found.</b></blockquote>")
        config.admin_states.pop(uid, None)

    elif state.get("step") == "tut_1":
        if not msg_text: return
        link = msg_text
        await db.update_settings({"tutorial_link": link})
        config.admin_states.pop(uid, None)
        await aio_reply(
            uid, 
            "<blockquote>"
            f"✅ <b>System tutorial link updated & activated:</b>\n"
            f"{link}"
            "</blockquote>"
        )

    elif state.get("step") == "ref_1":
        if not msg_text: return
        try:
            state["count"] = int(msg_text)
            state["step"] = "ref_2"
            await aio_reply(
                uid, 
                "<blockquote>"
                "📝 <b>Step 2:</b> Provide the custom invitation text (HTML supported)."
                "</blockquote>"
            )
        except ValueError:
            await aio_reply(
                uid, 
                "<blockquote>"
                "❌ <b>Invalid input:</b> Please provide a numeric value."
                "</blockquote>"
            )
    elif state.get("step") == "ref_2":
        if not msg_text: return
        state["text"] = msg_text
        state["step"] = "ref_3"
        await aio_reply(
            uid, 
            "<blockquote>"
            "⏱ <b>Final step:</b> Provide the premium duration reward (e.g., 7d, 1M, 24h)."
            "</blockquote>"
        )
    elif state.get("step") == "ref_3":
        if not msg_text: return
        if parse_duration(msg_text):
            await db.update_settings({"ref_system": True, "ref_count": state["count"], "ref_text": state["text"], "ref_time_str": msg_text})
            config.admin_states.pop(uid, None)
            await aio_reply(
                uid, 
                "<blockquote>"
                "✅ <b>Referral protocol configuration complete. System is now active.</b>"
                "</blockquote>"
            )
        else: 
            await aio_reply(
                uid, 
                "<blockquote>"
                "❌ <b>Invalid formatting:</b> Please utilize proper syntax (e.g., 7d, 1M)."
                "</blockquote>"
            )
