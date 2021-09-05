import os

class Config(object):
	API_HASH = os.getenv('API_HASH')
	BOT_TOKEN = os.getenv('BOT_TOKEN')
	API_ID = int(os.getenv('API_ID'))

	PROGRESS = """
Percentage : {0}%
Done: {1}
Total: {2}
Speed: {3}/s
ETA: {4}
"""
