from requests import get as rget
from __init__ import LOGGER
import os

CONFIG_FILE_URL = os.environ.get('https://gist.githubusercontent.com/yashoswalyo/3f101445fd6504c28d77d743a9f69f2d/raw/mergebot-config.env')
try:
    if len(CONFIG_FILE_URL) == 0:
        raise TypeError
    try:
        res = rget(CONFIG_FILE_URL)
        if res.status_code == 200:
            with open('config.env', 'wb+') as f:
                f.write(res.content)
        else:
            LOGGER.error(f"Failed to download config.env {res.status_code}")
    except Exception as e:
        LOGGER.error(f"CONFIG_FILE_URL: {e}")
except Exception as e:
    LOGGER.error(e)
    pass
