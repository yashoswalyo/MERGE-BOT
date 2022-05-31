from pyrogram import Client
import asyncio
from bot import UPLOAD_TO_DRIVE, UPLOAD_AS_DOC, formatDB, queueDB, gDict
from bot import delete_all
from pyrogram.types import CallbackQuery
from helpers import database
import os
import time
from helpers.display_progress import Progress
from helpers.ffmpeg import MergeSub, MergeVideo, take_screen_shot
from helpers.uploader import uploadVideo
from helpers.rclone_upload import rclone_driver, rclone_upload
from pyrogram.errors.rpc_error import UnknownError
from pyrogram.errors import MessageNotModified
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image


async def mergeNow(c: Client, cb: CallbackQuery, new_file_name: str):
    omess = cb.message.reply_to_message
    # print(omess.id)
    vid_list = list()
    sub_list = list()
    sIndex = 0
    await cb.message.edit("⭕ Processing...")
    duration = 0
    list_message_ids = queueDB.get(cb.from_user.id)["videos"]
    list_message_ids.sort()
    list_subtitle_ids = queueDB.get(cb.from_user.id)["subtitles"]
    # list_subtitle_ids.sort()
    print(list_message_ids, list_subtitle_ids)
    if list_message_ids is None:
        await cb.answer("Queue Empty", show_alert=True)
        await cb.message.delete(True)
        return
    if not os.path.exists(f"./downloads/{str(cb.from_user.id)}/"):
        os.makedirs(f"./downloads/{str(cb.from_user.id)}/")
    input_ = f"./downloads/{str(cb.from_user.id)}/input.txt"
    for i in await c.get_messages(
        chat_id=cb.from_user.id, message_ids=list_message_ids
    ):
        media = i.video or i.document
        await cb.message.edit(f"📥 Starting Download of ... `{media.file_name}`")
        print(f"📥 Starting Download of ... {media.file_name}")
        time.sleep(5)
        file_dl_path = None
        sub_dl_path = None
        try:
            c_time = time.time()
            prog = Progress(cb.from_user.id, c, cb.message)
            file_dl_path = await c.download_media(
                message=media,
                file_name=f"./downloads/{str(cb.from_user.id)}/{str(i.id)}/vid.mkv",  # fix for filename with single quote(') in name
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
            time.sleep(5)
        except UnknownError as e:
            print(e)
            pass
        except Exception as downloadErr:
            print(f"Failed to download Error: {downloadErr}")
            queueDB.get(cb.from_user.id)["video"].remove(i.id)
            await cb.message.edit("❗File Skipped!")
            time.sleep(4)
            continue

        if list_subtitle_ids[sIndex] is not None:
            a = await c.get_messages(
                chat_id=cb.from_user.id, message_ids=list_subtitle_ids[sIndex]
            )
            sub_dl_path = await c.download_media(
                message=a,
                file_name=f"./downloads/{str(cb.from_user.id)}/{str(a.id)}/",
            )
            print("Got sub: ", a.document.file_name)
            file_dl_path = await MergeSub(file_dl_path, sub_dl_path, cb.from_user.id)
            print("Added subs")
        sIndex += 1

        metadata = extractMetadata(createParser(file_dl_path))
        try:
            if metadata.has("duration"):
                duration += metadata.get("duration").seconds
            vid_list.append(f"file '{file_dl_path}'")
        except:
            await delete_all(root=f"./downloads/{str(cb.from_user.id)}")
            queueDB.update({cb.from_user.id: {"videos": [], "subtitles": []}})
            formatDB.update({cb.from_user.id: None})
            await cb.message.edit("⚠️ Video is corrupted")
            return

    _cache = list()
    for i in range(len(vid_list)):
        if vid_list[i] not in _cache:
            _cache.append(vid_list[i])
    vid_list = _cache
    await cb.message.edit(f"🔀 Trying to merge videos ...")
    with open(input_, "w") as _list:
        _list.write("\n".join(vid_list))
    merged_video_path = await MergeVideo(
        input_file=input_, user_id=cb.from_user.id, message=cb.message, format_="mkv"
    )
    if merged_video_path is None:
        await cb.message.edit("❌ Failed to merge video !")
        await delete_all(root=f"./downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": []}})
        formatDB.update({cb.from_user.id: None})
        return
    try:
        await cb.message.edit("✅ Sucessfully Merged Video !")
    except MessageNotModified:
        await cb.message.edit("Sucessfully Merged Video ! ✅")
    print(f"Video merged for: {cb.from_user.first_name} ")
    time.sleep(3)
    file_size = os.path.getsize(merged_video_path)
    os.rename(merged_video_path, new_file_name)
    await cb.message.edit(
        f"🔄 Renamed Merged Video to\n **{new_file_name.rsplit('/',1)[-1]}**"
    )
    time.sleep(2)
    merged_video_path = new_file_name
    if UPLOAD_TO_DRIVE[f"{cb.from_user.id}"]:
        await rclone_driver(omess, cb, merged_video_path)
        await delete_all(root=f"./downloads/{str(cb.from_user.id)}")
        queueDB.update({cb.from_user.id: {"videos": [], "subtitles": []}})
        formatDB.update({cb.from_user.id: None})
        return
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
        await cb.message.edit("⭕ Merged Video is corrupted")
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
