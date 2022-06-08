from dotenv import load_dotenv
load_dotenv(
    "config.env",
    override=True,
)
import asyncio
import os
import shutil
import string
import time
import shutil, psutil
import pyrogram
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from pyromod import listen

from config import Config
from helpers import database
from __init__ import (
    BROADCAST_MSG,
    LOGGER,
    gDict,
    UPLOAD_AS_DOC,
    UPLOAD_TO_DRIVE,
    queueDB,
    formatDB,
    replyDB,
)
from helpers.utils import get_readable_time, get_readable_file_size
from helpers.rclone_upload import rclone_driver, rclone_upload
import plugins.cb_handler

botStartTime = time.time()

mergeApp = Client(
    name="merge-bot",
    api_hash=Config.API_HASH,
    api_id=Config.API_ID,
    bot_token=Config.BOT_TOKEN,
    workers=300,
    app_version="3.0+yash-multiSubsSupport",
)
LOGGER.info("Bot started")


if os.path.exists("./downloads") == False:
    os.makedirs("./downloads")


@mergeApp.on_message(filters.command(["login"]) & filters.private)
async def allowUser(c: Client, m: Message):
    if await database.allowedUser(uid=m.from_user.id) is True:
        await m.reply_text(text=f"**Dont Spam**\n  ⚡ You can use me!!", quote=True)
    else:
        passwd = m.text.split(" ", 1)[1]
        if passwd == Config.PASSWORD:
            await database.allowUser(
                uid=m.from_user.id,
                fname=m.from_user.first_name,
                lname=m.from_user.last_name,
            )
            await m.reply_text(
                text=f"**Login passed ✅,**\n  ⚡ Now you can use me!!", quote=True
            )
        else:
            await m.reply_text(
                text=f"**Login failed ❌,**\n  🛡️ Unfortunately you can't use me\n\nContact: 🈲 @{Config.OWNER_USERNAME}",
                quote=True,
            )
    return


@mergeApp.on_message(
    filters.command(["stats"]) & filters.private & filters.user(Config.OWNER)
)
async def stats_handler(c: Client, m: Message):
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    stats = (
        f"<b>「 💠 BOT STATISTICS 」</b>\n"
        f"<b></b>\n"
        f"<b>⏳ Bot Uptime : {currentTime}</b>\n"
        f"<b>💾 Total Disk Space : {total}</b>\n"
        f"<b>📀 Total Used Space : {used}</b>\n"
        f"<b>💿 Total Free Space : {free}</b>\n"
        f"<b>🔺 Total Upload : {sent}</b>\n"
        f"<b>🔻 Total Download : {recv}</b>\n"
        f"<b>🖥 CPU : {cpuUsage}%</b>\n"
        f"<b>⚙️ RAM : {memory}%</b>\n"
        f"<b>💿 DISK : {disk}%</b>"
    )
    await m.reply_text(stats, quote=True)


@mergeApp.on_message(
    filters.command(["broadcast"]) & filters.private & filters.user(Config.OWNER)
)
async def broadcast_handler(c: Client, m: Message):
    msg = m.reply_to_message
    userList = await database.broadcast()
    len = userList.collection.count_documents({})
    status = await m.reply_text(text=BROADCAST_MSG.format(str(len), "0"), quote=True)
    success = 0
    for i in range(len):
        try:
            await msg.copy(chat_id=userList[i]["_id"])
            success = i + 1
            await status.edit_text(text=BROADCAST_MSG.format(len, success))
            LOGGER.info(f"Message sent to {userList[i]['name']} ")
        except FloodWait as e:
            await asyncio.sleep(e.x)
            await msg.copy(chat_id=userList[i]["_id"])
            LOGGER.info(f"Message sent to {userList[i]['name']} ")
        except InputUserDeactivated:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info(f"{userList[i]['_id']} - {userList[i]['name']} : deactivated\n")
        except UserIsBlocked:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info( f"{userList[i]['_id']} - {userList[i]['name']} : blocked the bot\n")
        except PeerIdInvalid:
            await database.deleteUser(userList[i]["_id"])
            LOGGER.info(f"{userList[i]['_id']} - {userList[i]['name']} : user id invalid\n")
        except Exception as err:
            LOGGER.warning(f"{err}\n")
        await asyncio.sleep(3)
    await status.edit_text(
        text=BROADCAST_MSG.format(len, success)
        + f"**Failed: {str(len-success)}**\n\n__🤓 Broadcast completed sucessfully__",
    )


@mergeApp.on_message(filters.command(["start"]) & filters.private)
async def start_handler(c: Client, m: Message):
    if m.from_user.id != Config.OWNER:
        await database.addUser(
            uid=m.from_user.id,
            fname=m.from_user.first_name,
            lname=m.from_user.last_name,
        )
        if await database.allowedUser(uid=m.from_user.id) is False:
            res = await m.reply_text(
                text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
                quote=True,
            )
            return
    res = await m.reply_text(
        text=f"Hi **{m.from_user.first_name}**\n\n ⚡ I am a file/video merger bot\n\n😎 I can merge Telegram files!, And upload it to telegram\n\n**Owner: 🈲 @{Config.OWNER_USERNAME}** ",
        quote=True,
    )


@mergeApp.on_message((filters.document | filters.video) & filters.private)
async def video_handler(c: Client, m: Message):
    if m.from_user.id != Config.OWNER:
        if await database.allowedUser(uid=m.from_user.id) is False:
            res = await m.reply_text(
                text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
                quote=True,
            )
            return
    input_ = f"downloads/{str(m.from_user.id)}/input.txt"
    if os.path.exists(input_):
        await m.reply_text("Sorry Bro,\nAlready One process in Progress!\nDon't Spam.")
        return
    media = m.video or m.document
    currentFileNameExt = media.file_name.rsplit(sep=".")[-1].lower()
    if media.file_name is None:
        await m.reply_text("File Not Found")
        return
    if media.file_name.rsplit(sep=".")[-1].lower() in "conf":
        await m.reply_text(
            text="**💾 Config file found, Do you want to save it?**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✅ Yes", callback_data=f"rclone_save"),
                        InlineKeyboardButton("❌ No", callback_data="rclone_discard"),
                    ]
                ]
            ),
            quote=True,
        )
        return

    if currentFileNameExt == "srt":
        queueDB.get(m.from_user.id)["videos"].append(m.id)
        queueDB.get(m.from_user.id)["subtitles"].append(None)

        button = await MakeButtons(c, m, queueDB)
        button.remove([InlineKeyboardButton("🔗 Merge Now", callback_data="merge")])
        button.remove([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])

        button.append(
            [InlineKeyboardButton("🔗 Merge Subtitles", callback_data="mergeSubtitles")]
        )
        button.append([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])
        await m.reply_text(
            text="You send a subtitle file. Do you want to merge it?",
            quote=True,
            reply_markup=InlineKeyboardMarkup(button),
        )
        formatDB.update({m.from_user.id: currentFileNameExt})
        return

    if queueDB.get(m.from_user.id, None) is None:
        formatDB.update({m.from_user.id: currentFileNameExt})
    if (formatDB.get(m.from_user.id, None) is not None) and (
        currentFileNameExt != formatDB.get(m.from_user.id)
    ):
        await m.reply_text(
            f"First you sent a {formatDB.get(m.from_user.id).upper()} file so now send only that type of file.",
            quote=True,
        )
        return
    if currentFileNameExt not in ["mkv", "mp4", "webm"]:
        await m.reply_text(
            "This Video Format not Allowed!\nOnly send MP4 or MKV or WEBM.", quote=True
        )
        return
    editable = await m.reply_text("Please Wait ...", quote=True)
    MessageText = "Okay,\nNow Send Me Next Video or Press **Merge Now** Button!"
    if queueDB.get(m.from_user.id, None) is None:
        queueDB.update({m.from_user.id: {"videos": [], "subtitles": []}})
    if (len(queueDB.get(m.from_user.id)["videos"]) >= 0) and (
        len(queueDB.get(m.from_user.id)["videos"]) < 10
    ):
        queueDB.get(m.from_user.id)["videos"].append(m.id)
        queueDB.get(m.from_user.id)["subtitles"].append(None)
        print(
            queueDB.get(m.from_user.id)["videos"],
            queueDB.get(m.from_user.id)["subtitles"],
        )
        if len(queueDB.get(m.from_user.id)["videos"]) == 1:
            await editable.edit("**Send me some more videos to merge them into single file**",)
            return
        if queueDB.get(m.from_user.id, None)["videos"] is None:
            formatDB.update(
                {m.from_user.id: media.file_name.split(sep=".")[-1].lower()}
            )
        if replyDB.get(m.from_user.id, None) is not None:
            await c.delete_messages(
                chat_id=m.chat.id, message_ids=replyDB.get(m.from_user.id)
            )
        if len(queueDB.get(m.from_user.id)["videos"]) == 10:
            MessageText = "Okay Unkil, Now Just Press **Merge Now** Button Plox!"
        markup = await MakeButtons(c, m, queueDB)
        reply_ = await editable.edit(
            text=MessageText, reply_markup=InlineKeyboardMarkup(markup)
        )
        replyDB.update({m.from_user.id: reply_.id})
    elif len(queueDB.get(m.from_user.id)["videos"]) > 10:
        markup = await MakeButtons(c, m, queueDB)
        await editable.text(
            "Max 10 videos allowed", reply_markup=InlineKeyboardMarkup(markup)
        )


@mergeApp.on_message(filters.photo & filters.private)
async def photo_handler(c: Client, m: Message):
    if m.from_user.id != Config.OWNER:
        if await database.allowedUser(uid=m.from_user.id) is False:
            res = await m.reply_text(
                text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
                quote=True,
            )
            return
    thumbnail = m.photo.file_id
    msg = await m.reply_text("Saving Thumbnail. . . .", quote=True)
    await database.saveThumb(m.from_user.id, thumbnail)
    LOCATION = f"./downloads/{m.from_user.id}_thumb.jpg"
    await c.download_media(message=m, file_name=LOCATION)
    await msg.edit_text(text="✅ Custom Thumbnail Saved!")


@mergeApp.on_message(filters.command(["help"]) & filters.private)
async def help_msg(c: Client, m: Message):
    await m.reply_text(
        text="""**Follow These Steps:

1) Send me the custom thumbnail (optional).
2) Send two or more Your Videos Which you want to merge
3) After sending all files select merge options
4) Select the upload mode.
5) Select rename if you want to give custom file name else press default**""",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close 🔐", callback_data="close")]]
        ),
    )


@mergeApp.on_message(filters.command(["about"]) & filters.private)
async def about_handler(c: Client, m: Message):
    await m.reply_text(
        text="""
- **WHAT'S NEW:**
+ Upload to drive using your own rclone config
+ Merged video preserves all streams of the first video you send (i.e. all audiotracks/subtitles)
- **FEATURES:**
+ Merge Upto 10 videos in one
+ Upload as document/video
+ Custom thumbnail support
+ Users can login to bot using password
+ Owner can broadcast message to all users
		""",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Developer", url="https://t.me/yashoswalyo")],
                [
                    InlineKeyboardButton(
                        "Source Code", url="https://github.com/yashoswalyo/MERGE-BOT"
                    ),
                    InlineKeyboardButton(
                        "Deployed By", url=f"https://t.me/{Config.OWNER_USERNAME}"
                    ),
                ],
            ]
        ),
    )


@mergeApp.on_message(filters.command(["showthumbnail"]) & filters.private)
async def show_thumbnail(c: Client, m: Message):
    try:
        thumb_id = await database.getThumb(m.from_user.id)
        LOCATION = f"./downloads/{m.from_user.id}_thumb.jpg"
        await c.download_media(message=str(thumb_id), file_name=LOCATION)
        if os.path.exists(LOCATION) is False:
            await m.reply_text(text="❌ Custom thumbnail not found", quote=True)
        else:
            await m.reply_photo(
                photo=LOCATION, caption="🖼️ Your custom thumbnail", quote=True
            )
    except Exception as err:
        await m.reply_text(text="❌ Custom thumbnail not found", quote=True)


@mergeApp.on_message(filters.command(["deletethumbnail"]) & filters.private)
async def delete_thumbnail(c: Client, m: Message):
    try:
        await database.delThumb(m.from_user.id)
        if os.path.exists(f"downloads/{str(m.from_user.id)}"):
            os.remove(f"downloads/{str(m.from_user.id)}")
        await m.reply_text("✅ Deleted Sucessfully", quote=True)
    except Exception as err:
        await m.reply_text(text="❌ Custom thumbnail not found", quote=True)


@mergeApp.on_callback_query()
async def callback(c: Client, cb: CallbackQuery):
    await plugins.cb_handler.cb_handler(c, cb)


async def showQueue(c: Client, cb: CallbackQuery):
    try:
        markup = await MakeButtons(c, cb.message, queueDB)
        await cb.message.edit(
            text="Okay,\nNow Send Me Next Video or Press **Merge Now** Button!",
            reply_markup=InlineKeyboardMarkup(markup),
        )
    except ValueError:
        await cb.message.edit("Send Some more videos")
    return


async def delete_all(root):
    try:
        shutil.rmtree(root)
    except Exception as e:
        print(e)


async def MakeButtons(bot: Client, m: Message, db: dict):
    markup = []
    for i in await bot.get_messages(
        chat_id=m.chat.id, message_ids=db.get(m.chat.id)["videos"]
    ):
        media = i.video or i.document or None
        if media is None:
            continue
        else:
            markup.append(
                [
                    InlineKeyboardButton(
                        f"{media.file_name}",
                        callback_data=f"showFileName_{i.id}",
                    )
                ]
            )
    markup.append([InlineKeyboardButton("🔗 Merge Now", callback_data="merge")])
    markup.append([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])
    return markup


if __name__ == "__main__":
    mergeApp.run()
