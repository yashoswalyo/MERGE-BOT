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



	api_hash='13d3e3bd0782827987a64acb1cc1d63b',
	api_id=1617207,
	bot_token='1983579380:AAGOwa3unThkzmmdRKZgFfPBVPI6bUMGUgQ'