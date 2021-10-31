import asyncio
import os
import shutil
import string
import time
import shutil, psutil

import pyrogram
from hachoir import metadata
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,InlineKeyboardMarkup, Message)
from pyromod import listen

from config import Config
from helpers import database
from helpers.display_progress import progress_for_pyrogram
from helpers.ffmpeg import MergeVideo
from helpers.uploader import uploadVideo
from helpers.utils import get_readable_time, get_readable_file_size
from helpers.rclone_upload import rclone_driver, rclone_upload

botStartTime = time.time()

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

@mergeApp.on_message( filters.command(['login']) & filters.private & ~filters.edited )
async def allowUser(c:Client, m: Message):
	passwd = m.text.split()[-1]
	if passwd == Config.PASSWORD:
		await database.allowUser(uid=m.from_user.id)
		await m.reply_text(
			text=f"**Login passed ✅,**\n  ⚡ Now you can you me!!",
			quote=True
		)
	else:
		await m.reply_text(
			text=f"**Login failed ❌,**\n  🛡️ Unfortunately you can't use me\n\nContact: 🈲 @{Config.OWNER_USERNAME}",
			quote=True
		)
	return

@mergeApp.on_message(filters.command(['stats']) & filters.private & filters.user(Config.OWNER))
async def stats_handler(c:Client, m:Message):
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>「 💠 BOT STATISTICS 」</b>\n' \
            f'<b></b>\n' \
            f'<b>⏳ Bot Uptime : {currentTime}</b>\n' \
            f'<b>💾 Total Disk Space : {total}</b>\n' \
            f'<b>📀 Total Used Space : {used}</b>\n' \
            f'<b>💿 Total Free Space : {free}</b>\n' \
            f'<b>🔺 Total Upload : {sent}</b>\n' \
            f'<b>🔻 Total Download : {recv}</b>\n' \
            f'<b>🖥 CPU : {cpuUsage}%</b>\n' \
            f'<b>⚙️ RAM : {memory}%</b>\n' \
            f'<b>💿 DISK : {disk}%</b>'
    await m.reply_text(stats,quote=True)

@mergeApp.on_message(filters.command(['broadcast']) & filters.private & filters.user(Config.OWNER))
async def broadcast_handler(c:Client, m:Message):
	msg = m.reply_to_message
	userList = await database.broadcast()
	len = userList.collection.count_documents({})
	for i in range(len):
		try:
			await msg.copy(chat_id=userList[i]['_id'])
		except FloodWait as e:
			await asyncio.sleep(e.x)
			await msg.copy(chat_id=userList[i]['_id'])
		except Exception:
			await database.deleteUser(userList[i]['_id'])
			pass
		print(f"Message sent to {userList[i]['name']} ")
		await asyncio.sleep(2)
	await m.reply_text(
		text="🤓 __Broadcast completed sucessfully__",
		quote=True
	)

@mergeApp.on_message(filters.command(['start']) & filters.private & ~filters.edited)
async def start_handler(c: Client, m: Message):
	await database.addUser(uid=m.from_user.id,fname=m.from_user.first_name, lname=m.from_user.last_name)
	if await database.allowedUser(uid=m.from_user.id) is False:
		res = await m.reply_text(
			text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
			quote=True
		)
		return
	res = await m.reply_text(
		text=f"Hi **{m.from_user.first_name}**\n\n ⚡ I am a file/video merger bot\n\n😎 I can merge Telegram files!, And upload it to telegram\n\n**Owner: 🈲 @{Config.OWNER_USERNAME}** ",
		quote=True
	)

	
@mergeApp.on_message((filters.document | filters.video) & filters.private & ~filters.edited)
async def video_handler(c: Client, m: Message):
	if await database.allowedUser(uid=m.from_user.id) is False:
		res = await m.reply_text(
			text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
			quote=True
		)
		return
	media = m.video or m.document
	if media.file_name is None:
		await m.reply_text('File Not Found')
		return
	if media.file_name.rsplit(sep='.')[-1].lower() in 'conf':
		await m.reply_text(
			text="**Config file found, Do you want to save it?**",
			reply_markup = InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton("✅ Yes", callback_data=f"rclone_save"),
						InlineKeyboardButton("❌ No", callback_data='rclone_discard')
					]
				]
			),
			quote=True
		)
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
			reply_markup=InlineKeyboardMarkup(markup),
			quote=True
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
	if await database.allowedUser(uid=m.from_user.id) is False:
		res = await m.reply_text(
			text=f"Hi **{m.from_user.first_name}**\n\n 🛡️ Unfortunately you can't use me\n\n**Contact: 🈲 @{Config.OWNER_USERNAME}** ",
			quote=True
		)
		return
	thumbnail = m.photo.file_id
	msg = await m.reply_text('Saving Thumbnail. . . .',quote=True)
	await database.saveThumb(m.from_user.id,thumbnail)
	LOCATION = f'./downloads/{m.from_user.id}_thumb.jpg'
	await c.download_media(
		message=m,
		file_name=LOCATION
	)
	await msg.edit_text(
		text="✅ Custom Thumbnail Saved!"
	)
	
@mergeApp.on_message(filters.command(['help']) & filters.private & ~filters.edited)
async def help_msg(c: Client, m: Message):
	await m.reply_text(
		text='''**Follow These Steps:

1) Send me the custom thumbnail (optional).
2) Send two or more Your Videos Which you want to merge
3) After sending all files select merge options
4) Select the upload mode.
5) Select rename if you want to give custom file name else press default**''',
		quote=True,
		reply_markup=InlineKeyboardMarkup(
			[ 
				[
					InlineKeyboardButton("Close 🔐", callback_data="close")
				]
			]
		)
	)

@mergeApp.on_message( filters.command(['about']) & filters.private & ~filters.edited )
async def about_handler(c:Client,m:Message):
	await m.reply_text(
		text='''
- **WHAT'S NEW:**
+ Upload to drive using your own rclone config
+ Merged video preserves all streams of the first video you send (i.e. all audiotracks/subtitles)
- **FEATURES:**
+ Merge Upto 10 videos in one 
+ Upload as document/video 
+ Custom thumbnail support
+ Users can login to bot using password
+ Owner can broadcast message to all users	
		''',
		quote=True,
		reply_markup=InlineKeyboardMarkup(
			[ 
				[ 
					InlineKeyboardButton("Developer", url="https://t.me/yashoswalyo")
				],
				[ 
					InlineKeyboardButton("Source Code", url="https://github.com/yashoswalyo/MERGE-BOT"),
					InlineKeyboardButton("Deployed By", url=f"https://t.me/{Config.OWNER_USERNAME}")
				]
			]
		)
	)

@mergeApp.on_message(filters.command(['showthumbnail']) & filters.private & ~filters.edited)
async def show_thumbnail(c:Client ,m: Message):
	try:
		thumb_id = await database.getThumb(m.from_user.id)
		LOCATION = f'./downloads/{m.from_user.id}_thumb.jpg'
		await c.download_media(message=str(thumb_id),file_name=LOCATION)
		if os.path.exists(LOCATION) is False:
			await m.reply_text(text='❌ Custom thumbnail not found',quote=True)
		else:
			await m.reply_photo(photo=LOCATION, caption='🖼️ Your custom thumbnail', quote=True)
	except Exception as err:
		await m.reply_text(text='❌ Custom thumbnail not found',quote=True)


@mergeApp.on_message(filters.command(['deletethumbnail']) & filters.private & ~filters.edited)
async def delete_thumbnail(c: Client,m: Message):
	try:
		thumb_id = await database.getThumb(m.from_user.id)
		LOCATION = f'./downloads/{m.from_user.id}_thumb.jpg'
		await c.download_media(message=str(thumb_id),file_name=LOCATION)
		if os.path.exists(LOCATION) is False:
			await m.reply_text(text='❌ Custom thumbnail not found',quote=True)
		else:
			await database.delThumb(m.from_user.id)
			os.remove(LOCATION)
			await m.reply_text('✅ Deleted Sucessfully',quote=True)
	except Exception as err:
		await m.reply_text(text='❌ Custom thumbnail not found',quote=True)
		

@mergeApp.on_callback_query()
async def callback(c: Client, cb: CallbackQuery):
	
	if cb.data == 'merge':
		await cb.message.edit(
			text='Where do you want to upload?',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('📤 To Telegram', callback_data = 'to_telegram'),
						InlineKeyboardButton('🌫️ To Drive', callback_data = 'to_drive')
					]
				]
			)
		)

	elif cb.data == 'to_drive':
		try:
			urc = await database.getUserRcloneConfig(cb.from_user.id)
			await c.download_media(message=urc,file_name=f"userdata/{cb.from_user.id}/rclone.conf")
		except Exception as err:
			await cb.message.reply_text("Rclone not Found, Unable to upload to drive")
		if os.path.exists(f"userdata/{cb.from_user.id}/rclone.conf") is False:
			await cb.message.delete()
			await delete_all(root=f"downloads/{cb.from_user.id}/")
			queueDB.update({cb.from_user.id: []})
			formatDB.update({cb.from_user.id: None})
			return 
		Config.upload_to_drive.update({f'{cb.from_user.id}':True})
		await cb.message.edit(
			text="Okay I'll upload to drive\nDo you want to rename? Default file name is **[@yashoswalyo]_merged.mkv**",
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					]
				]
			)
		)
	elif cb.data == 'to_telegram':
		Config.upload_to_drive.update({f'{cb.from_user.id}':False})
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
		Config.upload_as_doc.update({f'{cb.from_user.id}':True})
		await cb.message.edit(
			text='Do you want to rename? Default file name is **[@yashoswalyo]_merged.mkv**',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					]
				]
			)
		)
	elif cb.data == 'video':
		Config.upload_as_doc.update({f'{cb.from_user.id}':False})
		await cb.message.edit(
			text='Do you want to rename? Default file name is **[@yashoswalyo]_merged.mkv**',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					]
				]
			)
		)
	
	elif cb.data.startswith('rclone_'):
		if 'save' in cb.data:
			fileId = cb.message.reply_to_message.document.file_id
			print(fileId)
			await c.download_media(
				message=cb.message.reply_to_message,
				file_name=f"./userdata/{cb.from_user.id}/rclone.conf"
			)
			await database.addUserRcloneConfig(cb, fileId)
		else:
			await cb.message.delete()

	elif cb.data.startswith('rename_'):
		if 'YES' in cb.data:
			await cb.message.edit(
				'Current filename: **[@yashoswalyo]_merged.mkv**\n\nSend me new file name without extension: ',
				parse_mode='markdown'
			)
			res: Message = await c.listen( cb.message.chat.id, timeout=300 )
			if res.text :
				ascii_ = e = ''.join([i if (i in string.digits or i in string.ascii_letters or i == " ") else " " for i in res.text])
				new_file_name = f"./downloads/{str(cb.from_user.id)}/{ascii_.replace(' ', '_')}.mkv"
				await mergeNow(c,cb,new_file_name)
		if 'NO' in cb.data:
			await mergeNow(c,cb,new_file_name = f"./downloads/{str(cb.from_user.id)}/[@yashoswalyo]_merged.mkv")

	elif cb.data == 'cancel':
		await delete_all(root=f"downloads/{cb.from_user.id}/")
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		await cb.message.edit("Sucessfully Cancelled")
		await asyncio.sleep(5)
		await cb.message.delete(True)
		return
		
	elif cb.data == 'close':
		await cb.message.delete(True)

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
	omess = cb.message.reply_to_message
	# print(omess.message_id)
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
			await cb.message.edit(f'📥 Downloading...{media.file_name}')
			await asyncio.sleep(2)
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
	print(f"Video merged for: {cb.from_user.first_name} ")
	await asyncio.sleep(3)
	file_size = os.path.getsize(merged_video_path)
	os.rename(merged_video_path,new_file_name)
	await cb.message.edit(f"🔄 Renamed Merged Video to\n **{new_file_name.rsplit('/',1)[-1]}**")
	await asyncio.sleep(1)
	merged_video_path = new_file_name
	if Config.upload_to_drive[f'{cb.from_user.id}']:
		await rclone_driver(omess,cb,merged_video_path)
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		return
	if file_size > 2044723200:
		await cb.message.edit("Video is Larger than 2GB Can't Upload")
		await delete_all(root=f'./downloads/{cb.from_user.id}')
		queueDB.update({cb.from_user.id: []})
		formatDB.update({cb.from_user.id: None})
		return
	
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
		upload_mode=Config.upload_as_doc[f'{cb.from_user.id}']
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
