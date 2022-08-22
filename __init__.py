import os
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import time
import sys
from helpers.msg_utils import MakeButtons

"""Some Constants"""
MERGE_MODE = {}  # Maintain each user merge_mode
UPLOAD_AS_DOC = {}  # Maintain each user ul_type
UPLOAD_TO_DRIVE = {}  # Maintain each user drive_choice

FINISHED_PROGRESS_STR = os.environ.get("FINISHED_PROGRESS_STR", "█")
UN_FINISHED_PROGRESS_STR = os.environ.get("UN_FINISHED_PROGRESS_STR", "░")
EDIT_SLEEP_TIME_OUT = 10
gDict = defaultdict(lambda: [])
queueDB = {}
formatDB = {}
replyDB = {}

VIDEO_EXTENSIONS = ["mkv", "mp4", "webm", "ts", "wav", "mov"]
AUDIO_EXTENSIONS = ["aac", "ac3", "eac3", "m4a", "mka", "thd", "dts", "mp3"]
SUBTITLE_EXTENSIONS = ["srt", "ass"]

w = open("mergebotlog.txt", "w")
w.truncate(0)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("mergebotlog.txt", maxBytes=50000000, backupCount=10),
        logging.StreamHandler(sys.stdout),  # to get sys messages
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)
BROADCAST_MSG = """
**Total: {}
Done: {}**
"""
bMaker = MakeButtons()
