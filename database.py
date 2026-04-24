from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from config import Config

client = AsyncIOMotorClient(Config.MONGO_URL)
users = client.quitehub_bot.users
settings = client.quitehub_bot.settings
processed_media = client.quitehub_bot.processed_media

class db:
    @staticmethod
    async def is_media_processed(unique_id): 
        return await processed_media.find_one({"unique_id": unique_id}) is not None

    @staticmethod
    async def mark_media_processed(unique_id): 
        await processed_media.insert_one({"unique_id": unique_id, "timestamp": datetime.now()})

    @staticmethod
    async def get_user(user_id): 
        return await users.find_one({"user_id": user_id})

    @staticmethod
    async def add_user(user_id, nickname, inviter_id=None):
        await users.update_one({"user_id": user_id}, {"$set": {
            "user_id": user_id, "nickname": nickname, 
            "active_until": datetime.now() + timedelta(minutes=30),
            "is_premium": False, "premium_expiry": None, 
            "ref_balance": 0, "inviter": inviter_id,
            "total_sent": 0, "is_banned": False, "ban_expiry": None, 
            "last_reminded": datetime.min
        }}, upsert=True)

    @staticmethod
    async def remove_user(user_id): 
        await users.delete_one({"user_id": user_id})

    @staticmethod
    async def ban_user(user_id, days): 
        await users.update_one({"user_id": user_id}, {"$set": {"is_banned": True, "ban_expiry": datetime.now() + timedelta(days=days)}})

    @staticmethod
    async def unban_user(user_id): 
        await users.update_one({"user_id": user_id}, {"$set": {"is_banned": False, "ban_expiry": None}})

    @staticmethod
    async def update_activity(user_id):
        user = await db.get_user(user_id)
        if not user: return
        now = datetime.now()
        current_active = user.get("active_until", now)
        if current_active < now: current_active = now
        new_expiry = min(current_active + timedelta(minutes=30), now + timedelta(hours=24))
        await users.update_one({"user_id": user_id}, {"$set": {"active_until": new_expiry}, "$inc": {"total_sent": 1}})

    @staticmethod
    async def get_active_users():
        return await users.find({"is_banned": {"$ne": True}, "$or": [{"is_premium": True}, {"active_until": {"$gt": datetime.now()}}]}).to_list(length=None)

    @staticmethod
    async def get_stats():
        active = await users.count_documents({"is_banned": {"$ne": True}, "$or": [{"is_premium": True}, {"active_until": {"$gt": datetime.now()}}]})
        return await users.count_documents({}), active, await users.count_documents({"is_banned": True})

    @staticmethod
    async def get_bot_settings():
        s = await settings.find_one({"id": "global_config"})
        if not s:
            default = {"id": "global_config", "bin_channel": None, "pm_dlt": False, "dlt_time": 60, "ref_system": False, "ref_count": 5, "ref_text": "Invite!", "ref_time_str": "7d", "registration_open": True, "media_restriction": False}
            await settings.insert_one(default)
            return default
        return s

    @staticmethod
    async def update_settings(data): 
        await settings.update_one({"id": "global_config"}, {"$set": data}, upsert=True)

    @staticmethod
    async def remove_expired_premium(): 
        await users.update_many({"is_premium": True, "premium_expiry": {"$lt": datetime.now()}}, {"$set": {"is_premium": False, "premium_expiry": None}})

    @staticmethod
    async def remove_premium(user_id): 
        await users.update_one({"user_id": user_id}, {"$set": {"is_premium": False, "premium_expiry": None}})

    @staticmethod
    async def get_all_users(): 
        return await users.find({}).to_list(length=None)

    @staticmethod
    async def get_total_users_count(): 
        return await users.count_documents({})

    # 🔥 2-HOUR REMINDER SYSTEM LOGIC 🔥
    @staticmethod
    async def get_users_to_remind():
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        return await users.find({
            "is_premium": False, 
            "is_banned": {"$ne": True}, 
            "active_until": {"$lt": now}, 
            "last_reminded": {"$lt": two_hours_ago}
        }).to_list(length=None)

    @staticmethod
    async def update_reminded(user_id): 
        await users.update_one({"user_id": user_id}, {"$set": {"last_reminded": datetime.now()}})
