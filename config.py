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

    API_HASH = os.environ.get(
        "API_HASH",
        "b3051c4c2dfe4ef65f7146d172d3ddaf"
    )

    BOT_TOKEN = os.environ.get(
        "BOT_TOKEN",
        "8640588468:AAG_8Yrq9qTnXMi6M6gNSpkI4BwaUYUg14w"
    )

    MONGO_URL = os.environ.get(
        "MONGO_URL",
        "mongodb+srv://samplesamra:samplesamra@samplesamra.qtff1nr.mongodb.net/?appName=samplesamra"
    )

    DB_NAME = os.environ.get("DB_NAME", "quitehub_bot")

    LOG_ID = os.environ.get(
        "LOG_ID",
        "-1003959488076"
    )

    ADMIN_IDS = [8002345109]

    FORCE_SUB_CHANNEL = "-1003562811332"

    PENDING_RQUST_CHNL_ID = os.environ.get(
        "PENDING_RQUST_CHNL_ID",
        "-1004427611931"
    )

    PORT = int(os.environ.get("PORT", 8080))

    PING_URL = os.environ.get(
        "PING_URL",
        "http://0.0.0.0:8080"
    )

    MUTE_DURATION_HOURS = 12
    MUTE_PENALTY_MINUTES = 2

    ADJECTIVES = [
    "Shadow", "Dark", "Ghost", "Phantom", "Nova", "Cyber", "Elite", "Royal", "Alpha", "Omega", "Blaze", "Storm", "Frost", "Venom", "Titan", "Hyper", "Inferno", "Mystic", "Quantum", "Vortex", "Neon", "Silent", "Hidden", "Prime", "Apex", "Lunar", "Solar", "Crimson", "Obsidian", "Eclipse", "Thunder", "Rapid", "Turbo", "Ultra", "Zero", "Matrix", "Pixel", "Digital", "Astral", "Cosmic", "Atomic", "Velocity", "Fusion", "Spectral", "Legend", "Supreme", "Dynamic", "Infinite", "Genesis", "Nexus" 

    # Punjabi
    "Arclight", "Nightfall", "Voidwalker", "Starborn", "Ironclad",
"Skyforge", "Moonshade", "Frostbite", "Embercore", "Steelwing",
"Blackout", "Stormborn", "Firestorm", "Ashen", "Silverfang",
"Bloodmoon", "Darkstar", "Lightbringer", "Nether", "Riftwalker",
"Cloudstrike", "Stoneheart", "Sunflare", "Deepwave", "Wildfire",
"Nightshade", "Skyrunner", "Dreadnought", "Windrider", "Voidfang",
"Thunderstrike", "Soulforge", "Icebreaker", "Starfall", "Shadowbane",
"Ghostblade", "Ironwolf", "Firebrand", "Moonfang", "Stormcaller",
"Frostwing", "Dragonfire", "Voidstorm", "Skybreaker", "Solaris",
"Lunaris", "Eternis", "Aether", "Nebula", "Orbitron",
"Chronos", "Zenith", "Vertex", "Pulse", "Cipher",
"Helix", "Catalyst", "Paradox", "Mirage", "Tempest"

    # Hindi / North Indian
    "Alexander", "Victor", "Leon", "Damien", "Adrian",
"Sebastian", "Nathan", "Ethan", "Lucas", "Julian",
"Arthur", "Vincent", "Felix", "Oscar", "Caleb",
"Miles", "Silas", "Roman", "Theo", "Maxwell",
"Phoenix", "Atlas", "Orion", "Hunter", "Logan",
"Blake", "Carter", "Parker", "Zane", "Jaxon",
"Ryder", "Axel", "Mason", "Liam", "Noah",
"Elijah", "Aiden", "Kai", "Finn", "Xavier",
"Leo", "Jasper", "Rowan", "Asher", "Declan",
"Ezra", "Wyatt", "Nolan", "Tristan", "Grayson"

    # Extra Stylish / Attitude
    "Danger", "Monster", "Psycho", "Savage",
    "King", "Boss", "Emperor", "Mafia",
    "Sniper", "Hunter", "Killer", "Rider",
    "NoFear", "Fire", "Storm", "Thunder",
    "Dark", "Shadow", "Ghost", "Venom",
    "Alpha", "Wolf", "LionHeart", "Beast",
    "Turbo", "Nitro", "Diesel", "Petrolhead",
    "Speedy", "Roadster", "StreetKing",
    "Attitude", "RoyalBlood", "Heartless",
    "BadBoy", "Wanted", "Rowdy", "Khatarnak"
]

    NOUNS = [
    "Aetherix", "Nyxora", "Velcron", "Zerith", "Kaelix",
"Vortexa", "Dravix", "Xypher", "Noctaris", "Abylix",
"Zephiron", "Cryonix", "Vexaris", "Obscyra", "Nexora",
"Thalor", "Draxen", "Krylos", "Vorlix", "Azryth",
"Solvex", "Mythron", "Elarix", "Ravixor", "Xandor",
"Veltrix", "Zorvex", "Nythera", "Kairox", "Veyron",
"Drakonis", "Sylvex", "Auronix", "Zenthar", "Luxaris",
"Pyronex", "Valthor", "Xerion", "Kryvex", "Orlax",
"Zenovix", "Arcturon", "Duskara", "Elystrix", "Vexalon",
"Thornix", "Nebulor", "Axionis", "Zyphora", "Morvex",
"Rynox", "Veloria", "Kryndor", "Astrax", "Xyloris",
"Vortrix", "Nycron", "Zevoria", "Mythrax", "Ebonix"

    # Punjabi Style
    "Brimlock", "Cindrax", "Duskveil", "Etherforge", "Flintcore",
"Gravion", "Hexaris", "Ignivar", "Jadewing", "Korvax",
"Luxmere", "Mirethorn", "Nighthollow", "Oakspire", "Pyrelord",
"Quorin", "Runeblade", "Skylance", "Thornwake", "Umbrage",
"Verdantor", "Wyrmcrest", "Xalor", "Yonderfall", "Zarkon",
"Blackmarsh", "Crowhaven", "Driftwood", "Ebonreach", "Farshade",
"Gloomhart", "Hollowmere", "Ivorybane", "Jetstream", "Kingshade",
"Longstride", "Mournvale", "Northforge", "Oakenfall", "Palecrest",
"Quickthorn", "Redharbor", "Starhaven", "Truewind", "Umberfall",
"Valeguard", "Whisperwind", "Xenfall", "Yellowcrest", "Zincroft",
"Ashgrove", "Brightmoor", "Coldwater", "Dawnridge", "Eaglecrest",
"Foxglove", "Goldmere", "Highrock", "Ironbrook", "Juniper"

    # Hindi / Desi
    "Brightforge", "Stonewatch", "Windcrest", "Nightbrook",
"Silveroak", "Deepstone", "Ironvale", "Stormwatch",
"Goldleaf", "Mooncrest", "Swiftarrow", "Blueharbor",
"Ravenwood", "Winterhold", "Sunspire", "Frostvale",
"Oakshield", "Riverstone", "Starcrest", "Cloudbreaker",
"Emberwind", "Skyguard", "Wildgrove", "Ashwalker",
"Flarewing", "Dawnwatch", "Mistcaller", "Highcliff",
"Redstone", "Northwind", "Southridge", "Eastwatch",
"Westbrook", "Silentpeak", "Trueblade", "Stronghold",
"Brightwater", "Greyhawk", "Whiteoak", "Blackridge",
"Firebrand", "Steelheart", "Longbow", "Seawarden",
"Thunderpeak", "Crystalwind", "Wolfpine", "Eaglewatch",
"Shadowbrook", "Dragonstone", "Falconcrest", "Stormgate",
"Lightkeeper", "Stoneguard", "Moonwarden", "Ironcrest",
"Skybreaker", "Windrunner", "Riverguard", "Starwarden"

    # Stylish / Gaming / Internet
    "Beast", "Monster", "Hunter", "Sniper",
    "Killer", "Warrior", "Legend", "Shadow",
    "Ghost", "Venom", "Wolf", "Alpha",
    "Mafia", "Boss", "King", "Emperor",
    "Roadster", "StreetKing", "TurboRider",
    "NitroKing", "DarkKnight", "FireSoul",
    "StormBreaker", "ThunderBoy", "SavageBoy",
    "NoFear", "Heartless", "PsychoBoy",
    "DangerBoy", "WantedMunda", "RowdyKing"
]

    ADMIN_GOD_NAME = " 👑 Master Exx 💸"

    if BOT_TOKEN == "8660092184:AAEBYIU6lBaVvS8M6MK372UU9qDCExDNYAM":
        logger.warning(
            "Default BOT_TOKEN is being used. Ensure this is correct for production."
        )

    if MONGO_URL == "mongodb+srv://samplesamra:samplesamra@samplesamra.qtff1nr.mongodb.net/?appName=samplesamra":
        logger.warning(
            "Default MONGO_URL is being used. Ensure this is correct for production."
        )


START_TIME = time.time()

media_queue = None

album_cache = {}

admin_states = {}

chat_spam_tracker = {}

invite_links_cache = {}

pending_payments = {}
