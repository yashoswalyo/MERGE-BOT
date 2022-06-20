import os
from collections import defaultdict
import logging
from logging.handlers import RotatingFileHandler
import time
import sys

"""Some Constants"""
UPLOAD_AS_DOC = {}  # Maintain each user ul_type
UPLOAD_TO_DRIVE = {}  # Maintain each user drive_choice

FINISHED_PROGRESS_STR = os.environ.get("FINISHED_PROGRESS_STR", "█")
UN_FINISHED_PROGRESS_STR = os.environ.get("UN_FINISHED_PROGRESS_STR", "░")
EDIT_SLEEP_TIME_OUT = 10
gDict = defaultdict(lambda: [])
queueDB = {}
formatDB = {}
replyDB = {}


w = open('Merge-Bot.txt','w')
w.truncate(0)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("Merge-Bot.txt", maxBytes=50000000, backupCount=10),
        logging.StreamHandler(sys.stdout), #to get sys messages
    ],
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)
BROADCAST_MSG = '''
**Total: {}
Done: {}**
'''
