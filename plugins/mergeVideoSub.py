from pyrogram import Client
import asyncio
from bot import UPLOAD_AS_DOC, formatDB, queueDB, gDict
from bot import delete_all
from pyrogram.types import CallbackQuery
from helpers import database
import os
import time
from helpers.display_progress import Progress
from helpers.ffmpeg import MergeSubNew, take_screen_shot
from helpers.uploader import uploadVideo
from helpers.rclone_upload import rclone_driver, rclone_upload
from pyrogram.errors import MessageNotModified
from pyrogram.errors.rpc_error import UnknownError
from pyrogram.errors.exceptions.flood_420 import FloodWait
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image


async def mergeSub(c: Client, cb: CallbackQuery, new_file_name: str):
    print()
    omess = cb.message.reply_to_message
    vid_list = list()
    await cb.message.edit("⭕ Processing...")
    duration = 0
    list_message_ids = queueDB.get(cb.from_user.id)["videos"]
    list_message_ids.sort()
    if list_message_ids is None:
        await cb.answer("Queue Empty", show_alert=True)
        await cb.message.delete(True)
        return
    if not os.path.exists(f"./downloads/{str(cb.from_user.id)}/"):
        os.makedirs(f"./downloads/{str(cb.from_user.id)}/")
    for i in await c.get_messages(
        chat_id=cb.from_user.id, message_ids=list_message_ids
    ):
        media = i.video or i.document
        await cb.message.edit(f"📥 Starting Download of ... `{media.file_name}`")
        print(f"📥 Starting Download of ... {media.file_name}")
        time.sleep(5)
        file_dl_path = None
        try:
            c_time = time.time()
            prog = Progress(cb.from_user.id, c, cb.message)
            file_dl_path = await c.download_media(
                message=media,
                file_name=f"./downloads/{str(cb.from_user.id)}/{str(i.id)}/vid.mkv",
                progress=prog.progress_for_pyrogram,
                progress_args=(f"🚀 Downloading: `{media.file_name}`", c_time),
            )
            if (
                gDict[cb.message.chat.id]
                and cb.message.id in gDict[cb.message.chat.id]
            ):
                return
            await cb.message.edit(f"Downloaded Sucessfully ... `{media.file_name}`")
            print(f"Downloaded Sucessfully ... {media.file_name}")
            time.sleep(4)
        except Exception as downloadErr:
            print(f"Failed to download Error: {downloadErr}")
            queueDB.get(cb.from_user.id)["videos"].remove(i.id)
            await cb.message.edit("❗File Skipped!")
            time.sleep(4)
            await cb.message.delete(True)
            continue
        vid_list.append(f"{file_dl_path}")

    subbed_video = await MergeSubNew(
        filePath=vid_list[0],
        subPath=vid_list[1],
        user_id=cb.from_user.id,
        file_list=vid_list,
    )
    _cache = list()
    if subbed_video is None:
        await cb.message.edit("❌ Failed to add subs video !")
        await delete_all(root=f"./downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": []}})
        formatDB.update({cb.from_user.id: None})
        return
    try:
        await cb.message.edit("✅ Sucessfully Muxed Video !")
    except MessageNotModified:
        await cb.message.edit("Sucessfully Muxed Video ! ✅")
    print(f"Video muxed for: {cb.from_user.first_name} ")
    time.sleep(3)
    file_size = os.path.getsize(subbed_video)
    os.rename(subbed_video, new_file_name)
    await cb.message.edit(
        f"🔄 Renaming Video to\n **{new_file_name.rsplit('/',1)[-1]}**"
    )
    time.sleep(2)
    merged_video_path = new_file_name
    if file_size > 2044723200:
        await cb.message.edit("Video is Larger than 2GB Can't Upload")
        await delete_all(root=f"./downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": []}})
        formatDB.update({cb.from_user.id: None})
        return
    await cb.message.edit("🎥 Extracting Video Data ...")

    duration = 1
    try:
        metadata = extractMetadata(createParser(merged_video_path))
        if metadata.has("duration"):
            duration = metadata.get("duration").seconds
    except Exception as er:
        await delete_all(root=f"./downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": []}})
        formatDB.update({cb.from_user.id: None})
        await cb.message.edit("⭕ Merged Video is corrupted")
        return
    try:
        thumb_id = await database.getThumb(cb.from_user.id)
        video_thumbnail = f"./downloads/{str(cb.from_user.id)}_thumb.jpg"
        await c.download_media(message=str(thumb_id), file_name=video_thumbnail)
    except Exception as err:
        print("Generating thumb")
        video_thumbnail = await take_screen_shot(
            merged_video_path, f"downloads/{str(cb.from_user.id)}", (duration / 2)
        )
    width = 1280
    height = 720
    try:
        thumb = extractMetadata(createParser(video_thumbnail))
        height = thumb.get("height")
        width = thumb.get("width")
        img = Image.open(video_thumbnail)
        if width > height:
            img.resize((320, height))
        elif height > width:
            img.resize((width, 320))
        img.save(video_thumbnail)
        Image.open(video_thumbnail).convert("RGB").save(video_thumbnail, "JPEG")
    except:
        await delete_all(root=f"./downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": []}})
        formatDB.update({cb.from_user.id: None})
        await cb.message.edit(
            "⭕ Merged Video is corrupted \n\n<i>Try setting custom thumbnail</i>",
            parse_mode="html",
        )
        return
    await uploadVideo(
        c=c,
        cb=cb,
        merged_video_path=merged_video_path,
        width=width,
        height=height,
        duration=duration,
        video_thumbnail=video_thumbnail,
        file_size=os.path.getsize(merged_video_path),
        upload_mode=UPLOAD_AS_DOC[f"{cb.from_user.id}"],
    )
    await cb.message.delete(True)
    await delete_all(root=f"./downloads/{str(cb.from_user.id)}")
    queueDB.update({cb.from_user.id: {"videos": [], "subtitles": []}})
    formatDB.update({cb.from_user.id: None})
    return
