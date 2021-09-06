import asyncio
from config import Config
import os
import shutil
import string
import time

import pyrogram
from hachoir import metadata
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,InlineKeyboardMarkup, Message)
from pyromod import listen

from helpers.uploader import uploadVideo
from helpers.display_progress import progress_for_pyrogram
from helpers.ffmpeg import MergeVideo

mergeApp = Client(
	session_name="merge-bot",
	api_hash=Config.API_HASH,
	api_id=Config.API_ID,
	bot_token=Config.BOT_TOKEN,
	workers=300
)


if os.path.exists('./downloads') == False:
	os.makedirs('./downloads')


queueDB={}
formatDB={}
replyDB={}


@mergeApp.on_message(filters.command(['start']) & filters.private & ~filters.edited)
async def start_handler(c: Client, m: Message):
	if str(m.from_user.id) not in Config.ALD_USR:
		res = await m.reply_text(
			text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact:🈲 @{Config.OWNER_USERNAME}** ",
			quote=True
		)
		return
	res = await m.reply_text(
		text=f"Hi **{m.from_user.first_name}**\n\n ⚡ I am a file merger bot\n\n😎 I can merge Telegram files!, And upload it to telegram\n\n**Owner:🈲 @{Config.OWNER_USERNAME}** ",
		quote=True
	)
	
@mergeApp.on_message((filters.document | filters.video) & filters.private & ~filters.edited)
async def video_handler(c: Client, m: Message):
	if str(m.from_user.id) not in Config.ALD_USR:
		res = await m.reply_text(
			text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact:🈲 @{Config.OWNER_USERNAME}** ",
			quote=True
		)
		return
	media = m.video or m.document
	if media.file_name is None:
		await m.reply_text('File Not Found')
		return
	if media.file_name.split(sep='.')[-1].lower() not in ['mkv','mp4','webm']:
		await m.reply_text("This Video Format not Allowed!\nOnly send MP4 or MKV or WEBM.", quote=True)
		return
	if queueDB.get(m.from_user.id, None) is None:
		formatDB.update({m.from_user.id: media.file_name.rsplit(".", 1)[-1].lower()})
	editable = await m.reply_text("Please Wait ...", quote=True)
	MessageText = "Okay,\nNow Send Me Next Video or Press **Merge Now** Button!"
	if queueDB.get(m.from_user.id, None) is None:
		queueDB.update({m.from_user.id: []})
	if (len(queueDB.get(m.from_user.id)) >= 0) and (len(queueDB.get(m.from_user.id))<10 ):
		queueDB.get(m.from_user.id).append(m.message_id)
		if len(queueDB.get(m.from_user.id)) == 1:
			await editable.edit(
				'**Send me some more videos to merge them into single file**',parse_mode='markdown'
			)
			return
		if queueDB.get(m.from_user.id, None) is None:
			formatDB.update({m.from_user.id: media.file_name.split(sep='.')[-1].lower()})
		if replyDB.get(m.from_user.id, None) is not None:
			await c.delete_messages(chat_id=m.chat.id, message_ids=replyDB.get(m.from_user.id))
		if len(queueDB.get(m.from_user.id)) == 10:
			MessageText = "Okay Unkil, Now Just Press **Merge Now** Button Plox!"
		markup = await MakeButtons(c, m, queueDB)
		reply_ = await m.reply_text(
			text=MessageText,
			reply_markup=InlineKeyboardMarkup(markup)
		)
		replyDB.update({m.from_user.id: reply_.message_id})
	elif len(queueDB.get(m.from_user.id)) > 10:
		markup = await MakeButtons(c,m,queueDB)
		await editable.text(
			"Max 10 videos allowed",
			reply_markup=InlineKeyboardMarkup(markup)
		)

@mergeApp.on_message(filters.photo & filters.private & ~filters.edited)
async def photo_handler(c: Client,m: Message):
	if str(m.from_user.id) not in Config.ALD_USR:
		res = await m.reply_text(
			text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact:🈲 @{Config.OWNER_USERNAME}** ",
			quote=True
		)
		return
	thumbnail = m.photo.file_id
	msg = await m.reply_text('Saving Thumbnail. . . .',quote=True)
	LOCATION = f'./downloads/{m.from_user.id}_thumb.jpg'
	await c.download_media(
		message=m,
		file_name=LOCATION
	)
	await msg.edit_text(
		text="✅ Custom Thumbnail Saved!"
	)
	

@mergeApp.on_message(filters.command(['showthumbnail']) & filters.private & ~filters.edited)
async def show_thumbnail(c:Client ,m: Message):
	LOCATION = f'./downloads/{m.from_user.id}_thumb.jpg'
	if os.path.exists(LOCATION) is False:
		await m.reply_text(text='❌ Custom thumbnail not found',quote=True)
	else:
		await m.reply_photo(photo=LOCATION, caption='🖼️ Your custom thumbnail', quote=True)


@mergeApp.on_message(filters.command(['deletethumbnail']) & filters.private & ~filters.edited)
async def delete_thumbnail(c: Client,m: Message):
	LOCATION = f'./downloads/{m.from_user.id}_thumb.jpg'
	if os.path.exists(LOCATION) is False:
		await m.reply_text(text='❌ Custom thumbnail not found',quote=True)
	else:
		os.remove(LOCATION)
		await m.reply_text('✅ Deleted Sucessfully',quote=True)
		

@mergeApp.on_callback_query()
async def callback(c: Client, cb: CallbackQuery):
	if cb.data == 'merge':
		await cb.message.edit(
			text='How do yo want to upload file',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('🎞️ Video', callback_data='video'),
						InlineKeyboardButton('📁 File', callback_data='document')
					]
				]
			)
		)
	elif cb.data == 'document':
		Config.upload_as_doc = True
		await cb.message.edit(
			text='Do you want to rename? Default file name is **[@popcornmania]_merged.mkv**',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('Default', callback_data='rename_NO'),
						InlineKeyboardButton('Rename', callback_data='rename_YES')
					]
				]
			)
		)
	elif cb.data == 'video':
		await cb.message.edit(
			text='Do you want to rename? Default file name is **[@popcornmania]_merged.mkv**',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('Default', callback_data='rename_NO'),
						InlineKeyboardButton('Rename', callback_data='rename_YES')
					]
				]
			)
		)
	
	elif cb.data.startswith('rename_'):
		if 'YES' in cb.data:
			upload_as_doc = True
			await cb.message.edit(
				'Current filename: **[@popcornmania]_merged.mkv**\n\nSend me new file name: ',
				parse_mode='markdown'
			)
			res: Message = await c.listen( cb.message.chat.id, timeout=300 )
			if res.text :
				ascii_ = e = ''.join([i if (i in string.digits or i in string.ascii_letters or i == " ") else "" for i in res.text])
				new_file_name = f"./downloads/{str(cb.from_user.id)}/{ascii_.replace(' ', '_')}.mkv"
				await mergeNow(c,cb,new_file_name)
		if 'NO' in cb.data:
			await mergeNow(c,cb,new_file_name = f"./downloads/{str(cb.from_user.id)}/[@popcornmania]_merged.mkv")

	elif cb.data == 'cancel':
		await delete_all(root=f"downloads/{cb.from_user.id}/")
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		await cb.message.edit("Sucessfully Cancelled")
		await asyncio.sleep(5)
		await cb.message.delete(True)
		await cb.message.reply_to_message.delete(True)
		
			
	elif cb.data.startswith('showFileName_'):
		m = await c.get_messages(chat_id=cb.message.chat.id,message_ids=int(cb.data.rsplit("_",1)[-1]))
		try:
			await cb.message.edit(
				text=f"File Name: {m.video.file_name}",
				reply_markup=InlineKeyboardMarkup(
					[
						[
							InlineKeyboardButton("Remove",callback_data=f"removeFile_{str(m.message_id)}"),
							InlineKeyboardButton("Back", callback_data="back")
						]
					]
				)
			)
		except:
			await cb.message.edit(
				text=f"File Name: {m.document.file_name}",
				reply_markup=InlineKeyboardMarkup(
					[
						[
							InlineKeyboardButton("Remove",callback_data=f"removeFile_{str(m.message_id)}"),
							InlineKeyboardButton("Back", callback_data="back")
						]
					]
				)
			)
	
	elif cb.data == 'back':
		await showQueue(c,cb)

	elif cb.data.startswith('removeFile_'):
		queueDB.get(cb.from_user.id).remove(int(cb.data.split("_", 1)[-1]))
		await showQueue(c,cb)

async def showQueue(c:Client, cb: CallbackQuery):
	try:
		markup = await MakeButtons(c,cb.message,queueDB)
		await cb.message.edit(
			text="Okay,\nNow Send Me Next Video or Press **Merge Now** Button!",
			reply_markup=InlineKeyboardMarkup(markup)
		)
	except ValueError:
		await cb.message.edit('Send Some more videos')


async def mergeNow(c:Client, cb:CallbackQuery,new_file_name: str):
	vid_list = list()
	await cb.message.edit('⭕ Processing...')
	duration = 0
	list_message_ids = queueDB.get(cb.from_user.id,None)
	list_message_ids.sort()
	input_ = f"./downloads/{cb.from_user.id}/input.txt"
	if list_message_ids is None:
		await cb.answer("Queue Empty",show_alert=True)
		await cb.message.delete(True)
		return
	if not os.path.exists(f'./downloads/{cb.from_user.id}/'):
		os.makedirs(f'./downloads/{cb.from_user.id}/')
	for i in (await c.get_messages(chat_id=cb.from_user.id,message_ids=list_message_ids)):
		media = i.video or i.document
		try:
			await cb.message.edit(f'📥 Downloading...{media.file_name}',)
		except MessageNotModified :
			queueDB.get(cb.from_user.id).remove(i.message_id)
			await cb.message.edit("❗ File Skipped!")
			await asyncio.sleep(3)
			continue
		file_dl_path = None
		try:
			c_time = time.time()
			file_dl_path = await c.download_media(
				message=i,
				file_name=f"./downloads/{cb.from_user.id}/{i.message_id}/",
				progress=progress_for_pyrogram,
				progress_args=(
					'🚀 Downloading...',
					cb.message,
					c_time
				)
			)
		except Exception as downloadErr:
			print(f"Failed to download Error: {downloadErr}")
			queueDB.get(cb.from_user.id).remove(i.message_id)
			await cb.message.edit("❗File Skipped!")
			await asyncio.sleep(3)
			continue
		metadata = extractMetadata(createParser(file_dl_path))
		try:
			if metadata.has("duration"):
				duration += metadata.get('duration').seconds
			vid_list.append(f"file '{file_dl_path}'")
		except:
			await delete_all(root=f'./downloads/{cb.from_user.id}')
			queueDB.update({cb.from_user.id: []})
			formatDB.update({cb.from_user.id: None})
			await cb.message.edit('⚠️ Video is corrupted')
			return
	_cache = list()
	for i in range(len(vid_list)):
		if vid_list[i] not in _cache:
			_cache.append(vid_list[i])
	vid_list = _cache
	await cb.message.edit(f"🔀 Trying to merge videos ...")
	with open(input_,'w') as _list:
		_list.write("\n".join(vid_list))
	merged_video_path = await MergeVideo(
		input_file=input_,
		user_id=cb.from_user.id,
		message=cb.message,
		format_='mkv'
	)
	if merged_video_path is None:
		await cb.message.edit("❌ Failed to merge video !")
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		return
	await cb.message.edit("✅ Sucessfully Merged Video !")
	await asyncio.sleep(3)
	file_size = os.path.getsize(merged_video_path)
	if file_size > 2097152000:
		await cb.message.edit("Video is Larger than 2GB Can't Upload")
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		return
	await cb.message.edit(f"🔄 Renamed Merged Video to\n **{new_file_name.rsplit('/',1)[-1]}**")
	os.rename(merged_video_path,new_file_name)
	await asyncio.sleep(1)
	merged_video_path = new_file_name
	await cb.message.edit("🎥 Extracting Video Data ...")
	duration = 1
	width = 100
	height = 100
	try:
		metadata = extractMetadata(createParser(merged_video_path))
		if metadata.has("duration"):
			duration = metadata.get("duration").seconds
		if metadata.has("width"):
			width = metadata.get("width")
		if metadata.has("height"):
			height = metadata.get("height")
	except:
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		await cb.message.edit("⭕ Merged Video is corrupted")
		return
	video_thumbnail = f'./downloads/{cb.from_user.id}_thumb.jpg'
	if os.path.exists(video_thumbnail) is False:
		video_thumbnail=f"./assets/default_thumb.jpg"
	else: 
		Image.open(video_thumbnail).convert("RGB").save(video_thumbnail)
		img = Image.open(video_thumbnail)
		# img.resize(width,height)
		img.save(video_thumbnail,"JPEG")
	await uploadVideo(
		c=c,
		cb=cb,
		merged_video_path=merged_video_path,
		width=width,
		height=height,
		duration=duration,
		video_thumbnail=video_thumbnail,
		file_size=os.path.getsize(merged_video_path),
		upload_mode=Config.upload_as_doc
	)
	await cb.message.delete(True)
	await delete_all(root=f'./downloads/{cb.from_user.id}')
	queueDB.update({cb.from_user.id: []})
	formatDB.update({cb.from_user.id: None})
	return

async def delete_all(root):
	try:
		shutil.rmtree(root)
	except Exception as e:
		print(e)

async def MakeButtons(bot: Client, m: Message, db: dict):
	markup = []
	for i in (await bot.get_messages(chat_id=m.chat.id, message_ids=db.get(m.chat.id))):
		media = i.video or i.document or None
		if media is None:
			continue
		else:
			markup.append([InlineKeyboardButton(f"{media.file_name}", callback_data=f"showFileName_{str(i.message_id)}")])
	markup.append([InlineKeyboardButton("🔗 Merge Now", callback_data="merge")])
	markup.append([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])
	return markup



mergeApp.run()
