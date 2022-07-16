import time
from pyrogram import filters, Client as mergeApp
from pyrogram.types import Message, InlineKeyboardMarkup
from helpers.msg_utils import MakeButtons
from helpers.database import getUserMergeMode, setUserMergeMode


@mergeApp.on_message(filters.command(["s"]))
async def f1(c: mergeApp, m: Message):
    # setUserMergeMode(uid=m.from_user.id,mode=1)
    replay = await m.reply(text="Please wait", quote=True)
    await userSettings(
        replay, m.from_user.id, m.from_user.first_name, m.from_user.last_name
    )


async def userSettings(
    editable: Message, uid: int, fname: str | None, lname: str | None
):

    mode = getUserMergeMode(uid=uid)
    b = MakeButtons()
    if mode is not None:
        if mode== 1:
            userMergeModeId = 1
            userMergeModeStr = "Video + Video"
        elif mode == 2:
            userMergeModeId = 2
            userMergeModeStr = "Video + Audio"
        elif mode == 3:
            userMergeModeId = 3
            userMergeModeStr = "Video + Subtitle"

        uSettingsMessage = f"""
<b><u>Merge Bot settings for <a href='tg://user?id={uid}'>{fname} {lname}</a></u></b>

Merge mode: {userMergeModeStr}"""
        if userMergeModeId == 1:
            markup=b.makebuttons(
                ["Change to Video 🎥 + Audio 🎵", "Close"],
                [f"ch@ng3M0de_{uid}_2", "close"]
            )
        elif userMergeModeId == 2:
            markup=b.makebuttons(
                ["Change to Video 🎥 + Subtitle", "Close"],
                [f"ch@ng3M0de_{uid}_3", "close"]
            )
        elif userMergeModeId == 3:
            markup=b.makebuttons(
                ["Change to Video 🎥 + Video 🎥", "Close"],
                [f"ch@ng3M0de_{uid}_1", "close"]
            )
        res = await editable.edit(text=uSettingsMessage, reply_markup=InlineKeyboardMarkup(markup))
    else:
        setUserMergeMode(uid=int(uid), mode=1)
        await userSettings(editable, uid, fname, lname)
    # time.sleep(10)
    # await c.delete_messages(chat_id=editable.chat.id, message_ids=[res.id-1,res.id])
    return
