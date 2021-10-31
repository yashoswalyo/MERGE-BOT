# MERGE-BOT
### PR's welcomed
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

An Telegram Bot By [Yash Oswal](https://t.me/yashoswalyo) To Merge multiple Videos in Telegram into single video.

```diff
- WHAT'S NEW:
+ Upload Files to Drive
+ Merged video preserves all streams of the first video you send (i.e. all audiotracks/subtitles)

- FEATURES:
+ Merge Upto 10 videos in one 
+ Upload as document/video 
+ Custom thumbnail support
+ Users can login to bot using password
+ Owner can broadcast message to all users

- TO DO:
+ Option to add subtitles to telegram video
```

## Deploy(at your own risk) :
<p><a href="https://heroku.com/deploy?template=https://github.com/yashoswalyo/MERGE-BOT"><img src="https://img.shields.io/badge/Deploy%20To%20Heroku-blueviolet?style=for-the-badge&logo=heroku" width="200""/></a></p>

## Config Variables :
1. `API_ID` : User Account Telegram API_ID, get it from my.telegram.org
2. `API_HASH` : User Account Telegram API_HASH, get it from my.telegram.org
3. `BOT_TOKEN` : Your Telegram Bot Token, get it from @Botfather XD
4. `OWNER`: Enter bot owner's ID
5. `OWNER_USERNAME`: User name of bot owner
6. `DATABASE_URL`: Enter your mongodb URI
7. `PASSWORD`: Enter password to login bot

## Commands (add via @botfather) :
```sh
start - Start The Bot
showthumbnail - Shows your thumbnail
deletethumbnail - Delete your thumbnail
help - How to use Bot
login - Access bot
broadcast - (admin) Broadcast message to bot users
stats - check bots stats
```

## Self Host
```sh
$ git clone https://github.com/yashoswalyo/MERGE-BOT.git
$ cd MERGE-BOT
$ sudo apt-get install python3-pip ffmpeg
$ pip3 install -U pip
$ pip3 install -U -r requirements.txt
# <fill config.py correctly>
$ python3 bot.py
```

## License
```sh
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
- [Jigarvarma2005](https://github.com/Jigarvarma2005) for helping me to fix bugs 🤓
