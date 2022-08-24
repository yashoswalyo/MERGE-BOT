import os


class Config(object):
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    API_ID = os.environ.get("API_ID", "")
    OWNER = int(os.environ.get("OWNER"))
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME")
    PASSWORD = os.environ.get("PASSWORD")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    LOGCHANNEL =os.environ.get("LOGCHANNEL")  # Add channel id with -100 /\or/\ channel user name without @
