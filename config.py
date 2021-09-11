import os

class Config(object):
	API_HASH = os.getenv('API_HASH')
	BOT_TOKEN = os.getenv('BOT_TOKEN')
	API_ID = int(os.getenv('API_ID'))
	upload_as_doc = False
	ALD_USR = os.getenv('ALD_USR','')
	OWNER_USERNAME = os.getenv('OWNER_USERNAME')
	FLAG = int(os.getenv('FLAG',1))
	PROGRESS = """
Percentage : {0}%
Done: {1}
Total: {2}
Speed: {3}/s
ETA: {4}
"""
