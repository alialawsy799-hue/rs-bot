import os

# ===============================
#  إعدادات بوت جمهورية السادس
# ===============================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# يوزرنيم القناة بدون @
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "")

# آيدي الأدمنات (مفصولة بفاصلة في Railway)
_admins = os.environ.get("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admins.split(",") if x.strip()]

# اسم البوت
BOT_NAME = os.environ.get("BOT_NAME", "بوت جمهورية السادس")

# وصف البوت
BOT_DESCRIPTION = "بوتك التعليمي المخصص لطلاب السادس الإعدادي 📚"

# مسار قاعدة البيانات
DB_PATH = "data/bot.db"

# بروكسي (فارغ في Railway لأن الشبكة مفتوحة)
PROXY_URL = os.environ.get("PROXY_URL", "")
