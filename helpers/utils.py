# (c) dishapatel010
import pickle
import os.path
import os
import threading
import time
from helpers.database import setUserMergeSettings, getUserMergeSettings
# from magic import Magic
SIZE_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return "0B"
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f"{round(size_in_bytes, 2)}{SIZE_UNITS[index]}"
    except IndexError:
        return "File too large"

def get_mime_type(file_path):
    mime = 1
    mime_type = mime.from_file(file_path)
    mime_type = mime_type or "text/plain"
    return mime_type

def get_path_size(path: str):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            abs_path = os.path.join(root, f)
            total_size += os.path.getsize(abs_path)
    return total_size

def get_readable_time(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f"{days}d"
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f"{hours}h"
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f"{minutes}m"
    seconds = int(seconds)
    result += f"{seconds}s"
    return result
class UserSettings(object):
    def __init__(self, uid: int, name:str):
        self.user_id: int = uid
        self.name: str = name
        self.merge_mode: int = 1
        self.edit_metadata: bool = False
        self.allowed: bool = True
        self.thumbnail = None
        self.banned:bool = False
        self.get()
        # def __init__(self,uid:int,name:str,merge_mode:int=1,edit_metadata=False) -> None:

    def get(self):
        try:
            cur = getUserMergeSettings(self.user_id)
            if cur is not None:
                self.name = cur["name"]
                self.merge_mode = cur["user_settings"]["merge_mode"]
                self.edit_metadata = cur["user_settings"]["edit_metadata"]
                self.allowed = cur["isAllowed"]
                self.thumbnail = cur["thumbnail"]
                self.banned = cur["isBanned"]
                return {
                    "uid": self.user_id,
                    "name": self.name,
                    "user_settings": {
                        "merge_mode": self.merge_mode,
                        "edit_metadata": self.edit_metadata,
                    },
                    "isAllowed": self.allowed,
                    "isBanned": self.banned,
                    "thumbnail": self.thumbnail,
                }
            else: return self.set()
        except Exception:
            return self.set()

    def set(self):
        setUserMergeSettings(
            uid=self.user_id,
            name=self.name,
            mode=self.merge_mode,
            edit_metadata=self.edit_metadata,
            banned=self.banned,
            allowed=self.allowed,
            thumbnail=self.thumbnail,
        )
        return self.get()
