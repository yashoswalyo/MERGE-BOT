import time
import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton,InlineKeyboardMarkup,CallbackQuery
from helpers.display_progress import progress_for_pyrogram,humanbytes
from config import Config


async def uploadVideo(c: Client,cb: CallbackQuery,merged_video_path,width,height,duration,video_thumbnail,file_size,upload_mode:bool):
	try:
		sent_ = None
		if upload_mode is False:
			c_time = time.time()
			sent_ = await c.send_video(
				chat_id=cb.message.chat.id,
				video=merged_video_path,
				height=height,
				width=width,
				duration=duration,
				thumb=video_thumbnail,
				caption=f"**File Name: {merged_video_path.rsplit('/',1)[-1]}**",
				progress=progress_for_pyrogram,
				progress_args=(
					"Uploading file as video",
					cb.message,
					c_time
				)
			)
		else:
			c_time = time.time()
			sent_ = await c.send_document(
				chat_id=cb.message.chat.id,
				document=merged_video_path,
				thumb=video_thumbnail,
				caption=f"**File Name: {merged_video_path.rsplit('/',1)[-1]}**",
				progress=progress_for_pyrogram,
				progress_args=(
					"Uploading file as document",
					cb.message,
					c_time
				)
			)
	except Exception as err:
		print(err)
		await cb.message.edit("Failed to upload")
