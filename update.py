from requests import get as rget
from __init__ import LOGGER
import os
import subprocess
from dotenv import load_dotenv
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
