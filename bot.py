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
from pyrogram.errors.rpc_error import UnknownError
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,InlineKeyboardMarkup, Message)
from pyromod import listen

from config import Config
from helpers import database
from __init__ import LOGGER, gDict, UPLOAD_AS_DOC, UPLOAD_TO_DRIVE, queueDB, formatDB, replyDB
from helpers.display_progress import Progress
from helpers.ffmpeg import MergeSub, MergeVideo, MergeSubNew, take_screen_shot
from helpers.uploader import uploadVideo
from helpers.utils import get_readable_time, get_readable_file_size
from helpers.rclone_upload import rclone_driver, rclone_upload

botStartTime = time.time()

mergeApp = Client(
	session_name="merge-bot",
	api_hash=Config.API_HASH,
	api_id=Config.API_ID,
	bot_token=Config.BOT_TOKEN,
	workers=300,
	app_version="3.0+yash-multiSubsSupport"
)


if os.path.exists('./downloads') == False:
	os.makedirs('./downloads')




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
	input_ = f"downloads/{str(m.from_user.id)}/input.txt"
	if os.path.exists(input_):
		await m.reply_text("Sorry Bro,\nAlready One process in Progress!\nDon't Spam.")
		return
	media = m.video or m.document
	currentFileNameExt = media.file_name.rsplit(sep='.')[-1].lower()
	if media.file_name is None:
		await m.reply_text('File Not Found')
		return
	if media.file_name.rsplit(sep='.')[-1].lower() in 'conf':
		await m.reply_text(
			text="**💾 Config file found, Do you want to save it?**",
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

	if currentFileNameExt == 'srt':
		queueDB.get(m.from_user.id)['videos'].append(m.message_id)
		queueDB.get(m.from_user.id)['subtitles'].append(None)

		button = await MakeButtons(c,m,queueDB)
		button.remove([InlineKeyboardButton("🔗 Merge Now", callback_data="merge")])
		button.remove([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])

		button.append([InlineKeyboardButton("🔗 Merge Subtitles", callback_data="mergeSubtitles")])
		button.append([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])
		await m.reply_text(
			text="You send a subtitle file. Do you want to merge it?",
			quote=True,
			reply_markup= InlineKeyboardMarkup(button)
		)
		formatDB.update({m.from_user.id: currentFileNameExt})
		return

	if queueDB.get(m.from_user.id, None) is None:
		formatDB.update({m.from_user.id: currentFileNameExt})
	if (formatDB.get(m.from_user.id, None) is not None) and (currentFileNameExt != formatDB.get(m.from_user.id)):
		await m.reply_text(f"First you sent a {formatDB.get(m.from_user.id).upper()} file so now send only that type of file.", quote=True)
		return
	if currentFileNameExt not in ['mkv','mp4','webm']:
		await m.reply_text("This Video Format not Allowed!\nOnly send MP4 or MKV or WEBM.", quote=True)
		return
	editable = await m.reply_text("Please Wait ...", quote=True)
	MessageText = "Okay,\nNow Send Me Next Video or Press **Merge Now** Button!"
	if queueDB.get(m.from_user.id, None) is None:
		queueDB.update({m.from_user.id: {'videos':[],'subtitles':[]}})
	if (len(queueDB.get(m.from_user.id)['videos']) >= 0) and (len(queueDB.get(m.from_user.id)['videos'])<10 ):
		queueDB.get(m.from_user.id)['videos'].append(m.message_id)
		queueDB.get(m.from_user.id)['subtitles'].append(None)
		print(queueDB.get(m.from_user.id)['videos'], queueDB.get(m.from_user.id)['subtitles'])
		if len(queueDB.get(m.from_user.id)['videos']) == 1:
			await editable.edit(
				'**Send me some more videos to merge them into single file**',parse_mode='markdown'
			)
			return
		if queueDB.get(m.from_user.id, None)['videos'] is None:
			formatDB.update({m.from_user.id: media.file_name.split(sep='.')[-1].lower()})
		if replyDB.get(m.from_user.id, None) is not None:
			await c.delete_messages(chat_id=m.chat.id, message_ids=replyDB.get(m.from_user.id))
		if len(queueDB.get(m.from_user.id)['videos']) == 10:
			MessageText = "Okay Unkil, Now Just Press **Merge Now** Button Plox!"
		markup = await MakeButtons(c, m, queueDB)
		reply_ = await editable.edit(
			text=MessageText,
			reply_markup=InlineKeyboardMarkup(markup)
		)
		replyDB.update({m.from_user.id: reply_.message_id})
	elif len(queueDB.get(m.from_user.id)['videos']) > 10:
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
		await database.delThumb(m.from_user.id)
		if os.path.exists(f"downloads/{str(m.from_user.id)}"):
			os.remove(f"downloads/{str(m.from_user.id)}")
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
					],
					[InlineKeyboardButton("⛔ Cancel ⛔", callback_data="cancel")]
				]
			)
		)
		return

	elif cb.data == "mergeSubtitles":
		UPLOAD_TO_DRIVE.update({f'{cb.from_user.id}':False})
		await cb.message.edit(
			text='How do yo want to upload file',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('🎞️ Video', callback_data='videoS'),
						InlineKeyboardButton('📁 File', callback_data='documentS')
					],
					[InlineKeyboardButton("⛔ Cancel ⛔", callback_data="cancel")]
				]
			)
		)
		return

	elif cb.data == 'to_drive':
		try:
			urc = await database.getUserRcloneConfig(cb.from_user.id)
			await c.download_media(message=urc,file_name=f"userdata/{cb.from_user.id}/rclone.conf")
		except Exception as err:
			await cb.message.reply_text("Rclone not Found, Unable to upload to drive")
		if os.path.exists(f"userdata/{cb.from_user.id}/rclone.conf") is False:
			await cb.message.delete()
			await delete_all(root=f"downloads/{cb.from_user.id}/")
			queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
			formatDB.update({cb.from_user.id: None})
			return
		UPLOAD_TO_DRIVE.update({f'{cb.from_user.id}':True})
		await cb.message.edit(
			text="Okay I'll upload to drive\nDo you want to rename? Default file name is **[@yashoswalyo]_merged.mkv**",
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					],
					[InlineKeyboardButton("⛔ Cancel ⛔", callback_data="cancel")]
				]
			)
		)
		return
	
	elif cb.data == 'to_telegram':
		UPLOAD_TO_DRIVE.update({f'{cb.from_user.id}':False})
		await cb.message.edit(
			text='How do yo want to upload file',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('🎞️ Video', callback_data='video'),
						InlineKeyboardButton('📁 File', callback_data='document')
					],
					[InlineKeyboardButton("⛔ Cancel ⛔", callback_data="cancel")]
				]
			)
		)
		return
	
	elif cb.data == 'document':
		UPLOAD_AS_DOC.update({f'{cb.from_user.id}':True})
		await cb.message.edit(
			text='Do you want to rename? Default file name is **[@yashoswalyo]_merged.mkv**',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					],
					[InlineKeyboardButton("⛔ Cancel ⛔", callback_data="cancel")]
				]
			)
		)
		return
	
	elif cb.data == 'video':
		UPLOAD_AS_DOC.update({f'{cb.from_user.id}':False})
		await cb.message.edit(
			text='Do you want to rename? Default file name is **[@yashoswalyo]_merged.mkv**',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='rename_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='rename_YES')
					],
					[InlineKeyboardButton("⛔ Cancel ⛔", callback_data="cancel")]
				]
			)
		)
		return
	
	elif cb.data == 'documentS':
		UPLOAD_AS_DOC.update({f'{cb.from_user.id}':True})
		await cb.message.edit(
			text='Do you want to rename? Default file name is **[@yashoswalyo]_softmuxed_video.mkv**',
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='renameS_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='renameS_YES')
					],
					[InlineKeyboardButton("⛔ Cancel ⛔", callback_data="cancel")]
				]
			)
		)
		return
	
	elif cb.data == 'videoS':
		UPLOAD_AS_DOC.update({f'{cb.from_user.id}':False})
		await cb.message.edit(
			text=f"Do you want to rename? Default file name is **[@yashoswalyo]_softmuxed_video.mkv**",
			reply_markup=InlineKeyboardMarkup(
				[
					[
						InlineKeyboardButton('👆 Default', callback_data='renameS_NO'),
						InlineKeyboardButton('✍️ Rename', callback_data='renameS_YES')
					],
					[InlineKeyboardButton("⛔ Cancel ⛔", callback_data="cancel")]
				]
			)
		)
		return

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
		return

	elif cb.data.startswith('rename_'):
		if 'YES' in cb.data:
			await cb.message.edit(
				'Current filename: **[@yashoswalyo]_merged.mkv**\n\nSend me new file name without extension: You have 1 minute',
				parse_mode='markdown'
			)
			res: Message = await c.listen( cb.message.chat.id,filters=filters.text, timeout=60 )
			if res.text :
				new_file_name = f"./downloads/{str(cb.from_user.id)}/{res.text.replace(' ','_')}.mkv"
				await res.delete(True)
				await mergeNow(c,cb,new_file_name)
			return
		if 'NO' in cb.data:
			await mergeNow(c,cb,new_file_name = f"./downloads/{str(cb.from_user.id)}/[@yashoswalyo]_merged.mkv")

	elif cb.data.startswith('renameS_'):
		if 'YES' in cb.data:
			await cb.message.edit(
				'Current filename: **[@yashoswalyo]_softmuxed_video.mkv**\n\nSend me new file name without extension: You have 1 minute ',
				parse_mode='markdown'
			)
			res: Message = await c.listen( cb.message.chat.id,filters=filters.text, timeout=300 )
			if res.text :
				new_file_name = f"./downloads/{str(cb.from_user.id)}/{res.text.replace(' ','.')}.mkv"
				await res.delete(True)
				await mergeSub(c,cb,new_file_name)
		if 'NO' in cb.data:
			await mergeSub(c,cb,new_file_name = f"./downloads/{str(cb.from_user.id)}/[@yashoswalyo]_softmuxed_video.mkv")

	elif cb.data == 'cancel':
		await delete_all(root=f"downloads/{cb.from_user.id}/")
		queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
		formatDB.update({cb.from_user.id: None})
		await cb.message.edit("Sucessfully Cancelled")
		await asyncio.sleep(5)
		await cb.message.delete(True)
		return

	elif cb.data.startswith("gUPcancel"):
		cmf = cb.data.split("/")
		chat_id, mes_id, from_usr = cmf[1], cmf[2], cmf[3]
		if (int(cb.from_user.id) == int(from_usr)):
			await c.answer_callback_query(
				cb.id, text="Going to Cancel . . . 🛠", show_alert=False
			)
			gDict[int(chat_id)].append(int(mes_id))
		else:
			await c.answer_callback_query(
				callback_query_id=cb.id,
				text="⚠️ Opps ⚠️ \n I Got a False Visitor 🚸 !! \n\n 📛 Stay At Your Limits !!📛",
				show_alert=True,
				cache_time=0,
			)
		await delete_all(root=f"downloads/{cb.from_user.id}/")
		queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
		formatDB.update({cb.from_user.id: None})
		return

	elif cb.data == 'close':
		await cb.message.delete(True)

	elif cb.data.startswith('showFileName_'):
		id = int(cb.data.rsplit("_",1)[-1])
		print(queueDB.get(cb.from_user.id)['videos'],queueDB.get(cb.from_user.id)['subtitles'])
		sIndex = queueDB.get(cb.from_user.id)['videos'].index(id)
		m = await c.get_messages(chat_id=cb.message.chat.id,message_ids=id)
		if queueDB.get(cb.from_user.id)['subtitles'][sIndex] is None:
			try:
				await cb.message.edit(
					text=f"File Name: {m.video.file_name}",
					reply_markup=InlineKeyboardMarkup(
						[
							[
								InlineKeyboardButton("❌ Remove",callback_data=f"removeFile_{str(m.message_id)}"),
								InlineKeyboardButton("📜 Add Subtitle", callback_data=f"addSub_{str(sIndex)}")
							],
							[InlineKeyboardButton("🔙 Back", callback_data="back")]
						]
					)
				)
			except:
				await cb.message.edit(
					text=f"File Name: {m.document.file_name}",
					reply_markup=InlineKeyboardMarkup(
						[
							[
								InlineKeyboardButton("❌ Remove",callback_data=f"removeFile_{str(m.message_id)}"),
								InlineKeyboardButton("📜 Add Subtitle", callback_data=f"addSub_{str(sIndex)}")
							],
							[InlineKeyboardButton("🔙 Back", callback_data="back")]
						]
					)
				)
			return
		else:
			sMessId = queueDB.get(cb.from_user.id)['subtitles'][sIndex]
			s = await c.get_messages(chat_id=cb.message.chat.id,message_ids=sMessId)
			try:
				await cb.message.edit(
					text=f"File Name: {m.video.file_name}\n\nSubtitles: {s.document.file_name}",
					reply_markup=InlineKeyboardMarkup(
						[
							[
								InlineKeyboardButton("❌ Remove File",callback_data=f"removeFile_{str(m.message_id)}"),
								InlineKeyboardButton("❌ Remove Subtitle", callback_data=f"removeSub_{str(sIndex)}")
							],
							[InlineKeyboardButton("🔙 Back", callback_data="back")]
						]
					)
				)
			except:
				await cb.message.edit(
					text=f"File Name: {m.document.file_name}\n\nSubtitles: {s.document.file_name}",
					reply_markup=InlineKeyboardMarkup(
						[
							[
								InlineKeyboardButton("❌ Remove File",callback_data=f"removeFile_{str(m.message_id)}"),
								InlineKeyboardButton("❌ Remove Subtitle", callback_data=f"removeSub_{str(sIndex)}")
							],
							[InlineKeyboardButton("🔙 Back", callback_data="back")]
						]
					)
				)
			return
	
	elif cb.data.startswith('addSub_'):
		sIndex = int(cb.data.split(sep="_")[1])
		vMessId = queueDB.get(cb.from_user.id)["videos"][sIndex]
		rmess = await cb.message.edit(text=f"Send me a subtitle file, you have 1 minute",
			reply_markup=InlineKeyboardMarkup(
				[
					[InlineKeyboardButton("🔙 Back", callback_data=f"showFileName_{vMessId}")]
				]
			)
		)
		subs:Message = await c.listen(cb.message.chat.id,filters="filters.document",timeout=60)
		if subs is not None:
			media = subs.document or subs.video
			if media.file_name.rsplit(".")[-1] not in "srt":
				await subs.reply_text(text=f"Please go back first",
					reply_markup=InlineKeyboardMarkup(
						[
							[InlineKeyboardButton("🔙 Back", callback_data=f"showFileName_{vMessId}")]
						]
					),
					quote=True
				)
				return
			queueDB.get(cb.from_user.id)["subtitles"][sIndex] = subs.message_id
			await subs.reply_text(f"Added {subs.document.file_name}",
				reply_markup=InlineKeyboardMarkup(
					[
						[InlineKeyboardButton("🔙 Back", callback_data=f"showFileName_{vMessId}")]
					]
				),
				quote=True
			)
			await rmess.delete(True)
			print("Added sub to list")
		return

	elif cb.data.startswith('removeSub_'):
		sIndex = int(cb.data.rsplit("_")[-1])
		vMessId = queueDB.get(cb.from_user.id)["videos"][sIndex]
		queueDB.get(cb.from_user.id)["subtitles"][sIndex] = None
		await cb.message.edit(text=f"Subtitle Removed Now go back or send next video",
			reply_markup=InlineKeyboardMarkup(
				[
					[InlineKeyboardButton("🔙 Back", callback_data=f"showFileName_{vMessId}")]
				]
			)
		)
		print('Sub removed from list')
		return
	
	elif cb.data == 'back':
		await showQueue(c,cb)
		return

	elif cb.data.startswith('removeFile_'):
		sIndex = queueDB.get(cb.from_user.id)['videos'].index(int(cb.data.split("_", 1)[-1]))
		queueDB.get(cb.from_user.id)['videos'].remove(int(cb.data.split("_", 1)[-1]))
		await showQueue(c,cb)
		return

async def showQueue(c:Client, cb: CallbackQuery):
	try:
		markup = await MakeButtons(c,cb.message,queueDB)
		await cb.message.edit(
			text="Okay,\nNow Send Me Next Video or Press **Merge Now** Button!",
			reply_markup=InlineKeyboardMarkup(markup)
		)
	except ValueError:
		await cb.message.edit('Send Some more videos')
	return

async def mergeSub(c:Client,cb:CallbackQuery,new_file_name:str):
	print()
	omess = cb.message.reply_to_message
	vid_list = list()
	await cb.message.edit('⭕ Processing...')
	duration = 0
	list_message_ids = queueDB.get(cb.from_user.id)["videos"]
	list_message_ids.sort()
	if list_message_ids is None:
		await cb.answer("Queue Empty",show_alert=True)
		await cb.message.delete(True)
		return
	if not os.path.exists(f'./downloads/{str(cb.from_user.id)}/'):
		os.makedirs(f'./downloads/{str(cb.from_user.id)}/')
	for i in (await c.get_messages(chat_id=cb.from_user.id,message_ids=list_message_ids)):
		media = i.video or i.document
		await cb.message.edit(f'📥 Starting Download of ... `{media.file_name}`')
		print(f'📥 Starting Download of ... {media.file_name}')
		time.sleep(5)
		file_dl_path = None
		try:
			c_time = time.time()
			prog = Progress(cb.from_user.id,c,cb.message)
			file_dl_path = await c.download_media(
				message=i.document,
				file_name=f"./downloads/{str(cb.from_user.id)}/{str(i.message_id)}/vid.mkv",
				progress=prog.progress_for_pyrogram,
				progress_args=(
					f"🚀 Downloading: `{media.file_name}`",
					c_time
				)
			)
			if gDict[cb.message.chat.id] and cb.message.message_id in gDict[cb.message.chat.id]:
				return
			await cb.message.edit(f"Downloaded Sucessfully ... `{media.file_name}`")
			print(f"Downloaded Sucessfully ... {media.file_name}")
			time.sleep(4)
		except Exception as downloadErr:
			print(f"Failed to download Error: {downloadErr}")
			queueDB.get(cb.from_user.id)['videos'].remove(i.message_id)
			await cb.message.edit("❗File Skipped!")
			time.sleep(4)
			await cb.message.delete(True)
			continue
		vid_list.append(f"{file_dl_path}")

	subbed_video = await MergeSubNew(filePath=vid_list[0], subPath=vid_list[1],user_id=cb.from_user.id, file_list=vid_list)
	_cache = list()
	if subbed_video is None:
		await cb.message.edit("❌ Failed to add subs video !")
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
		formatDB.update({cb.from_user.id: None})
		return
	await cb.message.edit("✅ Sucessfully Muxed Video !")
	print(f"Video muxed for: {cb.from_user.first_name} ")
	await asyncio.sleep(3)
	file_size = os.path.getsize(subbed_video)
	os.rename(subbed_video,new_file_name)
	await cb.message.edit(f"🔄 Renaming Video to\n **{new_file_name.rsplit('/',1)[-1]}**")
	await asyncio.sleep(2)
	merged_video_path = new_file_name
	if file_size > 2044723200:
		await cb.message.edit("Video is Larger than 2GB Can't Upload")
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
		formatDB.update({cb.from_user.id: None})
		return
	await cb.message.edit("🎥 Extracting Video Data ...")

	duration = 1
	try:
		metadata = extractMetadata(createParser(merged_video_path))
		if metadata.has("duration"):
			duration = metadata.get("duration").seconds
	except Exception as er:
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
		formatDB.update({cb.from_user.id: None})
		await cb.message.edit("⭕ Merged Video is corrupted")
		return
	try:
		thumb_id = await database.getThumb(cb.from_user.id)
		video_thumbnail = f'./downloads/{str(cb.from_user.id)}_thumb.jpg'
		await c.download_media(message=str(thumb_id),file_name=video_thumbnail)
	except Exception as err:
		print("Generating thumb")
		video_thumbnail = await take_screen_shot(merged_video_path,f"downloads/{str(cb.from_user.id)}",(duration / 2))
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
			img.resize((width,320))
		img.save(video_thumbnail)
		Image.open(video_thumbnail).convert("RGB").save(video_thumbnail,"JPEG")
	except:
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
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
		upload_mode=UPLOAD_AS_DOC[f'{cb.from_user.id}']
	)
	await cb.message.delete(True)
	await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
	queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
	formatDB.update({cb.from_user.id: None})
	return


async def mergeNow(c:Client, cb:CallbackQuery,new_file_name: str):
	omess = cb.message.reply_to_message
	# print(omess.message_id)
	vid_list = list()
	sub_list = list()
	sIndex = 0
	await cb.message.edit('⭕ Processing...')
	duration = 0
	list_message_ids = queueDB.get(cb.from_user.id)["videos"]
	list_message_ids.sort()
	list_subtitle_ids = queueDB.get(cb.from_user.id)["subtitles"]
	# list_subtitle_ids.sort()
	print(list_message_ids,list_subtitle_ids)
	if list_message_ids is None:
		await cb.answer("Queue Empty",show_alert=True)
		await cb.message.delete(True)
		return
	if not os.path.exists(f'./downloads/{str(cb.from_user.id)}/'):
		os.makedirs(f'./downloads/{str(cb.from_user.id)}/')
	input_ = f"./downloads/{str(cb.from_user.id)}/input.txt"
	for i in (await c.get_messages(chat_id=cb.from_user.id,message_ids=list_message_ids)):
		media = i.video or i.document
		await cb.message.edit(f'📥 Starting Download of ... `{media.file_name}`')
		print(f'📥 Starting Download of ... {media.file_name}')
		time.sleep(5)
		file_dl_path = None
		sub_dl_path = None
		try:
			c_time = time.time()
			prog = Progress(cb.from_user.id,c,cb.message)
			file_dl_path = await c.download_media(
				message=media,
				file_name=f"./downloads/{str(cb.from_user.id)}/{str(i.message_id)}/vid.mkv", #fix for filename with single quote(') in name
				progress=prog.progress_for_pyrogram,
				progress_args=(
					f"🚀 Downloading: `{media.file_name}`",
					c_time
				)
			)
			if gDict[cb.message.chat.id] and cb.message.message_id in gDict[cb.message.chat.id]:
				return
			await cb.message.edit(f"Downloaded Sucessfully ... `{media.file_name}`")
			print(f"Downloaded Sucessfully ... {media.file_name}")
			time.sleep(5)
		except Exception as downloadErr:
			print(f"Failed to download Error: {downloadErr}")
			queueDB.get(cb.from_user.id)["video"].remove(i.message_id)
			await cb.message.edit("❗File Skipped!")
			time.sleep(4)
			continue
		except UnknownError as e:
			print("e")
			pass
		
		if list_subtitle_ids[sIndex] is not None:
			a = await c.get_messages(chat_id=cb.from_user.id,message_ids=list_subtitle_ids[sIndex])
			sub_dl_path = await c.download_media(message=a,file_name=f"./downloads/{str(cb.from_user.id)}/{str(a.message_id)}/")
			print("Got sub: ",a.document.file_name)
			file_dl_path = await MergeSub(file_dl_path,sub_dl_path,cb.from_user.id)
			print("Added subs")
		sIndex += 1

		metadata = extractMetadata(createParser(file_dl_path))
		try:
			if metadata.has("duration"):
				duration += metadata.get('duration').seconds
			vid_list.append(f"file '{file_dl_path}'")
		except:
			await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
			queueDB.update({cb.from_user.id: {"videos":[],"subtitles":[]}})
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
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {"videos":[],"subtitles":[]}})
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
	if UPLOAD_TO_DRIVE[f'{cb.from_user.id}']:
		await rclone_driver(omess,cb,merged_video_path)
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {"videos":[],"subtitles":[]}})
		formatDB.update({cb.from_user.id: None})
		return
	if file_size > 2044723200:
		await cb.message.edit("Video is Larger than 2GB Can't Upload")
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {"videos":[],"subtitles":[]}})
		formatDB.update({cb.from_user.id: None})
		return

	await cb.message.edit("🎥 Extracting Video Data ...")
	duration = 1
	try:
		metadata = extractMetadata(createParser(merged_video_path))
		if metadata.has("duration"):
			duration = metadata.get("duration").seconds
	except Exception as er:
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {'videos':[],'subtitles':[]}})
		formatDB.update({cb.from_user.id: None})
		await cb.message.edit("⭕ Merged Video is corrupted")
		return
	try:
		thumb_id = await database.getThumb(cb.from_user.id)
		video_thumbnail = f'./downloads/{str(cb.from_user.id)}_thumb.jpg'
		await c.download_media(message=str(thumb_id),file_name=video_thumbnail)
	except Exception as err:
		print("Generating thumb")
		video_thumbnail = await take_screen_shot(merged_video_path,f"downloads/{str(cb.from_user.id)}",(duration / 2))
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
			img.resize((width,320))
		img.save(video_thumbnail)
		Image.open(video_thumbnail).convert("RGB").save(video_thumbnail,"JPEG")
	except:
		await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
		queueDB.update({cb.from_user.id: {"videos":[],"subtitles":[]}})
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
		upload_mode=UPLOAD_AS_DOC[f'{cb.from_user.id}']
	)
	await cb.message.delete(True)
	await delete_all(root=f'./downloads/{str(cb.from_user.id)}')
	queueDB.update({cb.from_user.id: {"videos":[],"subtitles":[]}})
	formatDB.update({cb.from_user.id: None})
	return

async def delete_all(root):
	try:
		shutil.rmtree(root)
	except Exception as e:
		print(e)

async def MakeButtons(bot: Client, m: Message, db: dict):
	markup = []
	for i in (await bot.get_messages(chat_id=m.chat.id, message_ids=db.get(m.chat.id)['videos'])):
		media = i.video or i.document or None
		if media is None:
			continue
		else:
			markup.append([InlineKeyboardButton(f"{media.file_name}", callback_data=f"showFileName_{i.message_id}")])
	markup.append([InlineKeyboardButton("🔗 Merge Now", callback_data="merge")])
	markup.append([InlineKeyboardButton("💥 Clear Files", callback_data="cancel")])
	return markup


if __name__ == '__main__':	
	mergeApp.run()
