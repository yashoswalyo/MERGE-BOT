# (c) dishapatel010

import os
import threading
import time
from helpers.database import setUserMergeSettings, getUserMergeSettings
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
    def __init__(self, uid: int, name: str):
        self.user_id: int = uid
        self.name: str = name
        self.merge_mode: int = 1
        self.edit_metadata: bool = False
        self.allowed: bool = False
        self.thumbnail = None
        self.get()
        # def __init__(self,uid:int,name:str,merge_mode:int=1,edit_metadata=False) -> None:

    def get(self):
        cur = getUserMergeSettings(self.user_id)
        if cur is not None:
            self.name = cur["name"]
            self.merge_mode = cur["user_settings"]["merge_mode"]
            self.edit_metadata = cur["user_settings"]["edit_metadata"]
            self.allowed = cur["isAllowed"]
            self.thumbnail = cur["thumbnail"]
            return {
                "uid": self.user_id,
                "name": self.name,
                "user_settings": {
                    "merge_mode": self.merge_mode,
                    "edit_metadata": self.edit_metadata,
                },
                "isAllowed": self.allowed,
                "thumbnail": self.thumbnail,
            }
        else: return self.set()

    def set(self):
        setUserMergeSettings(
            uid=self.user_id,
            name=self.name,
            mode=self.merge_mode,
            edit_metadata=self.edit_metadata,
            allowed=self.allowed,
            thumbnail=self.thumbnail,
        )
        return self.get()
