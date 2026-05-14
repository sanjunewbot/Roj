import os
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("CONFIG")

class Config:
    API_ID = int(os.environ.get("API_ID", "22135296"))
    API_HASH = os.environ.get("API_HASH", "b3051c4c2dfe4ef65f7146d172d3ddaf")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8660092184:AAEBYIU6lBaVvS8M6MK372UU9qDCExDNYAM")
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://samplesamra:samplesamra@samplesamra.qtff1nr.mongodb.net/?appName=samplesamra")
    DB_NAME = os.environ.get("DB_NAME", "quitehub_bot")
    LOG_ID = os.environ.get("LOG_ID", "-1003959488076")

    ADMIN_IDS = [7893435873]
    FORCE_SUB_CHANNEL = "-1003843949677"
    PENDING_RQUST_CHNL_ID = os.environ.get("PENDING_RQUST_CHNL_ID", "-1004047659547")

    PORT = int(os.environ.get("PORT", 8080))
    PING_URL = os.environ.get("PING_URL", "http://0.0.0.0:8080")

    MUTE_DURATION_HOURS = 12
    MUTE_PENALTY_MINUTES = 2

    ADJECTIVES = [
    "Desi", "Punjab", "Mumbai", "Delhi", "Royal", "Gabru", "Jhakaas",
    "Bindaas", "Nawab", "Badshah", "Sultan", "Pataka", "Shikari",
    "Toofan", "Jatt", "Sarpanch", "Khalnayak", "Sherdil", "Dabang",
    "Raftaar", "Ziddi", "Gabbar", "Veer", "Yoddha", "Singham",
    "Bhau", "Tapori", "Mast", "Dhakad", "Chulbul", "Akhanda",
    "Rangeela", "Jhakkas", "Lafandar", "Teekha", "Mirchi",
    "Baazigar", "Junglee", "Tashan", "Bindass", "Rangbaaz",
    "Befikra", "Diler", "Hindustani", "Patiala", "Ludhiana",
    "Haryana", "Rajasthani", "Bambaiya", "Banarasi", "Lucknawi"
]

NOUNS = [
    "Jatt", "Gabru", "Sher", "Baaz", "Yoddha", "Rakshak",
    "Toofan", "Aatank", "Pataka", "Sultan", "Badshah",
    "Nawab", "Bhau", "Tapori", "Daku", "Khalnayak",
    "Mirchi", "Raftaar", "Bijli", "Bullet", "Shera",
    "Gabbar", "Don", "Sarpanch", "Launda", "Munda",
    "Veer", "Pahalwan", "Fauji", "Sipahi", "Raja",
    "Maharaja", "Thakur", "Pandit", "Chaudhary", "Patel",
    "Naik", "Banda", "Tiger", "Singham", "Baazigar",
    "Rider", "Driver", "Raider", "Player", "Mastana",
    "Bawandar", "Diler", "Rangebaaz", "Lafandar", "Jhakkas"
]
    ADMIN_GOD_NAME = "🜲 𝕲𝖔𝖉 𝕺𝖋 𝕭𝖔𝖙 🜲"

    if BOT_TOKEN == "8660092184:AAEBYIU6lBaVvS8M6MK372UU9qDCExDNYAM":
        logger.warning("Default BOT_TOKEN is being used. Ensure this is correct for production.")
    if MONGO_URL == "mongodb+srv://samplesamra:samplesamra@samplesamra.qtff1nr.mongodb.net/?appName=samplesamra":
        logger.warning("Default MONGO_URL is being used. Ensure this is correct for production.")

START_TIME = time.time()
media_queue = None
album_cache = {}
admin_states = {}
chat_spam_tracker = {}
invite_links_cache = {}
pending_payments = {}
