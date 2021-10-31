from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pyrogram.types import CallbackQuery

from config import Config

class db(object):
	client = MongoClient(Config.DATABASE_URL)
	mergebot = client.MergeBot

async def addUser(uid,fname,lname):
	try:
		userDetails = {
			'_id': uid,
			'name': f"{fname} {lname}",
		}
		db.mergebot.users.insert_one(userDetails)
		print(f"New user added id={uid}\n{fname} {lname} \n")
	except DuplicateKeyError:
		print(f"Duplicate Entry Found for id={uid}\n{fname} {lname} \n")
	return

async def broadcast():
	a = db.mergebot.users.find({})
	return a

async def allowUser(uid):
	a = db.mergebot.allowedUsers.insert_one(
		{'_id':uid,}
	)

async def allowedUser(uid):
	a = db.mergebot.allowedUsers.find_one({'_id':uid})
	try:
		if uid == a['_id']:
			return True
	except TypeError:	
		return False

async def saveThumb(uid,fid):
	try:
		db.mergebot.thumbnail.insert_one({
			'_id':uid,
			'thumbid':fid
		})
	except DuplicateKeyError:
		db.mergebot.thumbnail.replace_one(
			{'_id':uid},
			{'thumbid':fid}
		)

async def delThumb(uid):
	db.mergebot.thumbnail.delete_many({
		'_id':uid
	})

async def getThumb(uid):
	res = db.mergebot.thumbnail.find_one({"_id":uid})
	return res['thumbid']

async def deleteUser(uid):
	db.mergebot.allowedUsers.delete_many({'_id':uid})
	db.mergebot.users.delete_many({'_id':uid})


async def addUserRcloneConfig(cb:CallbackQuery, fileId):
	try:
		await cb.message.edit("Adding file to DB")
		uid = cb.from_user.id
		db.mergebot.rcloneData.insert_one({
			'_id':uid,
			'rcloneFileId':fileId
		})
	except Exception as err:
		print("Updating rclone")
		await cb.message.edit("Updating file in DB")
		uid = cb.from_user.id
		db.mergebot.rcloneData.replace_one(
			{'_id':uid},
			{'rcloneFileId':fileId}
		)
	await cb.message.edit("Done")
	return

async def getUserRcloneConfig(uid):
	try:
		res = db.mergebot.rcloneData.find_one({'_id':uid})
		return res['rcloneFileId'] 
	except Exception as err:
		return None
