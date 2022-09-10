from requests import get as rget
from __init__ import LOGGER
import os
import subprocess
from dotenv import load_dotenv

CONFIG_FILE_URL = os.environ.get('CONFIG_FILE_URL')
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
load_dotenv(
    "config.env",
    override=True,
)
# tired of redeploying :(
UPSTREAM_REPO = os.environ.get('UPSTREAM_REPO')
UPSTREAM_BRANCH = os.environ.get('UPSTREAM_BRANCH')
try:
    if len(UPSTREAM_REPO) == 0:
       raise TypeError
except:
    UPSTREAM_REPO = None
try:
    if len(UPSTREAM_BRANCH) == 0:
       raise TypeError
except:
    UPSTREAM_BRANCH = 'master'

if UPSTREAM_REPO is not None:
    if os.path.exists('.git'):
        subprocess.run(["rm", "-rf", ".git"])

    update = subprocess.run([f"git init -q \
                     && git config --global user.email yashoswal18@gmail.com \
                     && git config --global user.name mergebot \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)

    if update.returncode == 0:
        LOGGER.info('Successfully updated with latest commit from UPSTREAM_REPO')
    else:
        LOGGER.warning('Something went wrong while updating, check UPSTREAM_REPO if valid or not!')
