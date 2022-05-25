import os
import time
import asyncio
from pyrogram import Client
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from helpers.display_progress import Progress
from config import Config


async def uploadVideo(
    c: Client,
    cb: CallbackQuery,
    merged_video_path,
    width,
    height,
    duration,
    video_thumbnail,
    file_size,
    upload_mode: bool,
):
    try:
        sent_ = None
        prog = Progress(cb.from_user.id, c, cb.message)
        if upload_mode is False:
            c_time = time.time()
            sent_: Message = await c.send_video(
                chat_id=cb.message.chat.id,
                video=merged_video_path,
                height=height,
                width=width,
                duration=duration,
                thumb=video_thumbnail,
                caption=f"`{merged_video_path.rsplit('/',1)[-1]}`",
                progress=prog.progress_for_pyrogram,
                progress_args=(
                    f"Uploading: `{merged_video_path.rsplit('/',1)[-1]}`",
                    c_time,
                ),
            )
        else:
            c_time = time.time()
            sent_: Message = await c.send_document(
                chat_id=cb.message.chat.id,
                document=merged_video_path,
                thumb=video_thumbnail,
                caption=f"`{merged_video_path.rsplit('/',1)[-1]}`",
                progress=prog.progress_for_pyrogram,
                progress_args=(
                    f"Uploading: `{merged_video_path.rsplit('/',1)[-1]}`",
                    c_time,
                ),
            )
    except Exception as err:
        print(err)
        await cb.message.edit("Failed to upload")
    if sent_ is not None:
        if Config.LOGCHANNEL is not None:
            media = sent_.video or sent_.document
            await sent_.copy(
                chat_id=Config.LOGCHANNEL,
                caption=f"`{media.file_name}`\n\nMerged for: {cb.from_user.mention}",
            )
