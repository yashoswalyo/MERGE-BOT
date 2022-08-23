# MERGE-BOT
### PR's Welcomed
<br>

![GitHub Repo stars](https://img.shields.io/github/stars/yashoswalyo/MERGE-BOT?color=blue&style=flat)
![GitHub forks](https://img.shields.io/github/forks/yashoswalyo/MERGE-BOT?color=green&style=flat)
![GitHub issues](https://img.shields.io/github/issues/yashoswalyo/MERGE-BOT)
![GitHub closed issues](https://img.shields.io/github/issues-closed/yashoswalyo/MERGE-BOT)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yashoswalyo/MERGE-BOT)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/yashoswalyo/MERGE-BOT)
![GitHub contributors](https://img.shields.io/github/contributors/yashoswalyo/MERGE-BOT?style=flat)
![GitHub repo size](https://img.shields.io/github/repo-size/yashoswalyo/MERGE-BOT?color=red)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/yashoswalyo/MERGE-BOT)

An Telegram Bot By [Yash Oswal](https://t.me/yashoswalyo) To Merge multiple Videos in Telegram into single video. <br>
Bugs should be reported at: [Telegram Group](https://t.me/yo_codes_support)

```diff
- TODO's:
+ Add ability to edit metadata of exported video

- FEATURES:
+ (new) Option to add multiple audio tracks to telegram video
+ (new) Option to add multiple subtitles to telegram video
+ Upload Files to Drive (Send your rclone config to bot)
#  1. Send your rclone config to bot.
#  2. Then send videos to merge, after you tap "Merge Now", upload to drive option will available.
+ Merged video preserves all streams of the first video you send (i.e. all audiotracks/subtitles)

+ Merge Upto 10 videos in one 
+ Upload as document/video 
+ Custom thumbnail support
+ Users can login to bot using password
+ Owner can broadcast message to all users
+ Log Channel to store all merged videos

```
## Deploy Tutorial : 
[![Watch the video](https://img.youtube.com/vi/H-xVk_4zccs/hqdefault.jpg)](https://youtu.be/H-xVk_4zccs)

## Deploy(at your own risk) :
<p><a href="https://heroku.com/deploy?template=https://github.com/yashoswalyo/MERGE-BOT"><img src="https://img.shields.io/badge/Deploy%20To%20Heroku-blueviolet?style=for-the-badge&logo=heroku" width="200""/></a></p>

### OR
Goto `settings > actions > secret > New Repository Secret` <br>
Add `HEROKU_EMAIL` <br>
Add `HEROKU_API_KEY` <br>
Add `HEROKU_APP_NAME` <br>
Add `CONFIG_FILE_URL` <br>
Goto `Actions > Manual Deploy To Heroku > Run Workflow`

### OR
Coming soon
## Tutorial to get MongoDB URI:
[![Watch the video](https://img.youtube.com/vi/OfQ7xxMylV4/hqdefault.jpg)](https://youtu.be/OfQ7xxMylV4)


## Config File Variables :
1. `TELEGRAM_API` : User Account Telegram API_ID, get it from my.telegram.org
2. `API_HASH` : User Account Telegram API_HASH, get it from my.telegram.org
3. `BOT_TOKEN` : Your Telegram Bot Token, get it from @Botfather XD
4. `OWNER`: Enter bot owner's ID
5. `OWNER_USERNAME`: User name of bot owner
6. `DATABASE_URL`: Enter your mongodb URI
7. `PASSWORD`: Enter password to login bot
8. `LOGCHANNEL`: Log channel will store all users merged videos ("-100" + "channel Id")
9. `USER_SESSION_STRING`: Premium account session string to upload upto 4GB (requires `LOGCHANNEL`)


## Commands (add via @botfather) :
```
start - Start The Bot
showthumbnail - Shows your thumbnail
deletethumbnail - Delete your thumbnail
settings - User Settings to manage different modes
help - How to use Bot
about - About the bot
login - Access bot
log - (admin only) Get log file from server
broadcast - (admin only) Broadcast message to bot users
stats - (admin only) check bots stats
```

## Self Host
```sh
$ git clone https://github.com/yashoswalyo/MERGE-BOT.git
$ cd MERGE-BOT
$ sudo apt-get install python3 python3-pip ffmpeg
$ pip3 install -U pip
$ pip3 install -U -r requirements.txt
# <fill config.env correctly by looking at sample_config.env>
$ bash start.sh
```

## License
```
Merge Bot, Telegram Video Merge Bot
Copyright (c) 2021  Yash Oswal <https://github.com/yashoswalyo>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
```

## Credits

- [Me](https://github.com/yashoswalyo) for [Nothing](https://github.com/yashoswalyo/MERGE-BOT) 😬
- [Dan](https://github.com/delivrance) for [Pyrogram](https://github.com/pyrogram/pyrogram) ❤️
- [Abir Hasan](https://github.com/AbirHasan2005) for his wonderful [code](https://github.com/AbirHasan2005/VideoMerge-Bot) ❤️
- [Jigarvarma2005](https://github.com/Jigarvarma2005) and [SpechIDE](https://t.me/spechide) for helping me to fix bugs 🤓
