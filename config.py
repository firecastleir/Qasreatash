import os

SITE = os.environ.get("WP_SITE", "https://firecastle.ir").rstrip("/")
WP_USER = os.environ["WP_USER"]
WP_APP_PASSWORD = os.environ["WP_APP_PASSWORD"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
# draft = پیش‌نویس (برای بازبینی) | publish = انتشار مستقیم
POST_STATUS = os.environ.get("POST_STATUS", "draft")
# FaridNeural = مرد ، DilaraNeural = زن
VOICE = os.environ.get("VOICE", "fa-IR-FaridNeural")
VOICE_RATE = os.environ.get("VOICE_RATE", "-4%")

BRAND = "شومینه قصر آتش"
PHONE = "02144278518"
MOBILE = "09031413301"
WORKSHOP = "تهران، پل ساوه، خیابان غفاری ۳، پلاک ۴"
OFFICE = "تهران، ستارخان، خیابان اسدی، خیابان قدیانی، پلاک ۴۳، واحد ۸"
