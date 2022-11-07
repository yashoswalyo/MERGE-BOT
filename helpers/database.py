from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pyrogram.types import CallbackQuery
from config import Config
from __init__ import LOGGER, MERGE_MODE, LOCAL_SETTINGS_DB, RCLONE_LOCAL_DB


# class Database(object):
#    client = MongoClient(Config.DATABASE_URL)
#    mergebot = client.MergeBot


async def addUser(uid, fname, lname):
    try:
        userDetails = {
            "_id": uid,
            "name": f"{fname} {lname}",
        }
        Database.mergebot.users.insert_one(userDetails)
        LOGGER.info(f"New user added id={uid}\n{fname} {lname} \n")
    except DuplicateKeyError:
        LOGGER.info(f"Duplicate Entry Found for id={uid}\n{fname} {lname} \n")
    return


async def broadcast():
    a = Database.mergebot.mergeSettings.find({})
    return a


async def allowUser(uid, fname, lname):
    try:
        a = Database.mergebot.allowedUsers.insert_one(
            {
                "_id": uid,
            }
        )
    except DuplicateKeyError:
        LOGGER.info(f"Duplicate Entry Found for id={uid}\n{fname} {lname} \n")
    return


async def allowedUser(uid):
    a = Database.mergebot.allowedUsers.find_one({"_id": uid})
    try:
        if uid == a["_id"]:
            return True
    except TypeError:
        return False


async def saveThumb(uid, fid):
    try:
        Database.mergebot.thumbnail.insert_one({"_id": uid, "thumbid": fid})
    except DuplicateKeyError:
        Database.mergebot.thumbnail.replace_one({"_id": uid}, {"thumbid": fid})


async def delThumb(uid):
    Database.mergebot.thumbnail.delete_many({"_id": uid})
    return True


async def getThumb(uid):
    res = Database.mergebot.thumbnail.find_one({"_id": uid})
    return res["thumbid"]


async def deleteUser(uid):
    Database.mergebot.mergeSettings.delete_many({"_id": uid})


async def addUserRcloneConfig(cb: CallbackQuery, fileId):
    try:
        await cb.message.edit("Adding file to DB")
        uid = cb.from_user.id
        RCLONE_LOCAL_DB.update({uid: {"_id": uid, "rcloneFileId": fileId}})
        # Database.mergebot.rcloneData.insert_one({"_id": uid, "rcloneFileId": fileId})
    except Exception as err:
        LOGGER.info("Updating rclone")
        await cb.message.edit("Updating file in DB")
        uid = cb.from_user.id
        RCLONE_LOCAL_DB.update({uid: {"_id": uid, "rcloneFileId": fileId}})
        # Database.mergebot.rcloneData.replace_one({"_id": uid}, {"rcloneFileId": fileId})
    await cb.message.edit("Done")
    return


async def getUserRcloneConfig(uid):
    try:
        # res = Database.mergebot.rcloneData.find_one({"_id": uid})
        res = RCLONE_LOCAL_DB.get(uid)
        return res["rcloneFileId"]
    except Exception as err:
        return None


def getUserMergeSettings(uid: int):
    if LOCAL_SETTINGS_DB.get(uid) is None:
        LOGGER.info(f"{uid} Not found")
        return None
    return LOCAL_SETTINGS_DB.get(uid)


def setUserMergeSettings(
    uid: int, name: str, mode, edit_metadata, banned, allowed, thumbnail
):
    modes = Config.MODES
    if uid:
        LOCAL_SETTINGS_DB.update(
            {
                uid: {
                    "_id": uid,
                    "name": name,
                    "user_settings": {
                        "merge_mode": mode,
                        "edit_metadata": edit_metadata,
                    },
                    "isAllowed": allowed,
                    "isBanned": banned,
                    "thumbnail": thumbnail,
                }
            }
        )
        LOGGER.info(
            "User {} - {}Settings updated: {}".format(
                uid, name, LOCAL_SETTINGS_DB.get(uid)
            )
        )


def enableMetadataToggle(uid: int, value: bool):

    1


def disableMetadataToggle(uid: int, value: bool):
    1
