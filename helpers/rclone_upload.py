import os
import re
import subprocess
import time
import asyncio
import json
import traceback
from pyrogram.client import Client
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import CallbackQuery, Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helpers import database
from __init__ import LOGGER


class Status:
    # Shared List
    Tasks = []

    def __init__(self):
        self._task_id = len(self.Tasks) + 1

    def refresh_info(self):
        raise NotImplementedError

    def update_message(self):
        raise NotImplementedError

    def is_active(self):
        raise NotImplementedError

    def set_inactive(self):
        raise NotImplementedError


class RCUploadTask(Status):
    def __init__(self, task):
        super().__init__()
        self.Tasks.append(self)
        self._dl_task = task
        self._active = True
        self._upmsg = ""
        self._prev_cont = ""
        self._message = None
        self._error = ""
        self._omess = None
        self.cancel = False

    async def set_original_message(self, omess):
        self._omess = omess

    async def get_original_message(self):
        return self._omess

    async def get_sender_id(self):
        return self._omess.sender_id

    async def set_message(self, message):
        self._message = message

    async def refresh_info(self, msg):
        # The rclone is process dependent so cant be updated here.
        self._upmsg = msg

    async def create_message(self):
        mat = re.findall("Transferred:.*ETA.*", self._upmsg)
        nstr = mat[0].replace("Transferred:", "")
        nstr = nstr.strip()
        nstr = nstr.split(",")
        prg = nstr[1].strip("% ")
        prg = "Progress:- {} - {}%".format(self.progress_bar(prg), prg)
        progress = "<b>Uploaded:- {} \n{} \nSpeed:- {} \nETA:- {}</b> \n<b>Using Engine:- </b><code>RCLONE</code>".format(
            nstr[0], prg, nstr[2], nstr[3].replace("ETA", "")
        )
        return progress

    def progress_bar(self, percentage):
        """Returns a progress bar for download"""
        # percentage is on the scale of 0-1
        comp = "●"
        ncomp = "○"
        pr = ""

        try:
            percentage = int(percentage)
        except:
            percentage = 0

        for i in range(1, 11):
            if i <= int(percentage / 10):
                pr += comp
            else:
                pr += ncomp
        return pr

    async def update_message(self):
        progress = await self.create_message()
        if not self._prev_cont == progress:
            # kept just in case
            self._prev_cont = progress
            try:
                await self._message.edit(
                    progress,
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
                    ),
                )
            except MessageNotModified as e:
                LOGGER.info("{}".format(e))
            except FloodWait as e:
                LOGGER.info("{}".format(e))
            except Exception as e:
                LOGGER.info("Not expected {}".format(e))

    async def is_active(self):
        return self._active

    async def set_inactive(self, error=None):
        self._active = False
        if error is not None:
            self._error = error


async def rclone_driver(userMess: Message, cb: CallbackQuery, merged_video_path):
    conf_path = f"./userdata/{cb.from_user.id}/rclone.conf"
    dl_task = None
    ul_task = RCUploadTask(dl_task)
    DRIVE_NAME = (
        open(conf_path, "r").readlines()[0].removesuffix("]\n").removeprefix("[")
    )
    BASE_DIR = "/"
    edtime = 5
    try:
        return await rclone_upload(
            merged_video_path,
            userMess,
            cb,
            cb.message,
            DRIVE_NAME,
            BASE_DIR,
            edtime,
            conf_path,
            ul_task,
        )
    except Exception as er:
        await ul_task.set_inactive()
        LOGGER.info("Stuff gone wrong in here: " + str(er))
        return


async def rclone_upload(
    merged_video_path: str,
    userMess: Message,
    cb: CallbackQuery,
    mess: Message,
    DRIVE_NAME,
    BASE_DIR,
    edTime,
    conf_path: str,
    task: RCUploadTask,
):
    a = 1
    await task.set_original_message(userMess)
    data = "upcancel {}".format(cb.from_user.id)
    msg: Message = await mess.reply_text(
        "**Uploading to configured drive.... will be updated soon.**",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
        ),
    )
    await task.set_message(msg)
    rclone_copy_cmd = [
        "rclone",
        "copy",
        f"--config={conf_path}",
        str(merged_video_path),
        f"{DRIVE_NAME}:{BASE_DIR}",
        "-f",
        "- *.!qB",
        "--buffer-size=1M",
        "-P",
    ]
    rclonePr = subprocess.Popen(rclone_copy_cmd, stdout=subprocess.PIPE)
    rcloneResult = await rclone_process_display(
        rclonePr, edTime, msg, mess, userMess, task
    )
    if rcloneResult is False:
        await mess.edit(f"{mess.text} \n Canceled Rclone Upload")
        await msg.delete()
        rclonePr.kill()
        task.cancel = True
        return task

    LOGGER.info("Upload Complete")
    gid = await getGdriveLink(
        driveName=DRIVE_NAME,
        baseDir=BASE_DIR,
        entName=os.path.basename(merged_video_path),
        conf_path=conf_path,
        isdir=False,
    )
    file_link = f"https://drive.google.com/file/d/{gid[0]}/view"
    button = [InlineKeyboardButton("Drive url", url=file_link)]
    await cb.message.reply_text(
        text=f"**UPLOADED FILE :-**\n<code>{os.path.basename(merged_video_path)}</code>\nTo Drive.",
        reply_markup=InlineKeyboardMarkup([button]),
    )

    LOGGER.info(f"Uploaded folder id: {gid}")
    await msg.delete()
    return task


async def rclone_process_display(
    process: subprocess.Popen,
    edit_time,
    msg: Message,
    mess: Message,
    userMess: Message,
    task: RCUploadTask,
):
    blank = 0  #
    sleeps = False  #
    start = time.time()  # Get current time
    while True:
        data: str = process.stdout.readline().decode()
        data = data.strip()
        mat = re.findall("Transferred:.*ETA.*", data)
        if mat is not None:
            if len(mat) > 0:
                sleeps = True
                if time.time() - start > edit_time:
                    start = time.time()
                    await task.refresh_info(data)
                    await task.update_message()

        if data == "":
            blank += 1
            if blank == 20:
                break
        else:
            blank = 0

        if sleeps:
            sleeps = False
            await asyncio.sleep(2)
            process.stdout.flush()


async def getGdriveLink(driveName, baseDir, entName: str, conf_path: str, isdir=True):
    LOGGER.info("Ent - ", entName)
    entName = re.escape(entName)
    filter_path = os.path.join(os.getcwd(), str(time.time()).replace(".", "") + ".txt")
    # with open(filter_path,'w',encoding="UTF-8") as file:
    # 	file.write(f"+ {entName}\n")
    # 	file.write(f"- *")
    get_id_cmd = [
        "rclone",
        "lsjson",
        f"--config={conf_path}",
        f"{driveName}:{baseDir}",
        "--files-only",
        "-f",
        f"+ {entName}",
        "-f",
        "- *",
    ]
    # piping only stdout
    process = await asyncio.create_subprocess_exec(
        *get_id_cmd, stdout=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()
    stdout = stdout.decode().strip()

    if os.path.exists(filter_path):
        os.remove(filter_path)

    try:
        data = json.loads(stdout)
        id = data[0]["ID"]
        name = data[0]["Name"]
        return (id, name)
    except Exception:
        LOGGER.info(f"Error occured: {traceback.format_exc()} {stdout} ")
