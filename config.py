import os
import time

class Config:
    API_ID = int(os.environ.get("API_ID", "22135296"))
    API_HASH = os.environ.get("API_HASH", "b3051c4c2dfe4ef65f7146d172d3ddaf")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8660092184:AAEBYIU6lBaVvS8M6MK372UU9qDCExDNYAM")
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://samplesamra:samplesamra@samplesamra.qtff1nr.mongodb.net/?appName=samplesamra")
    
    ADMIN_IDS = [7893435873]
    FORCE_SUB_CHANNEL = "-1003843949677"
    PENDING_RQUST_CHNL_ID = os.environ.get("PENDING_RQUST_CHNL_ID", "-1004047659547")
    
    PORT = int(os.environ.get("PORT", 8080))
    PING_URL = os.environ.get("PING_URL", "http://0.0.0.0:8080")
    
    MUTE_DURATION_HOURS = 12
    MUTE_PENALTY_MINUTES = 2

START_TIME = time.time()
media_queue = None
album_cache = {}
admin_states = {}
chat_spam_tracker = {}
invite_links_cache = {}
