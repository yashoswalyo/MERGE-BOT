import asyncio
import subprocess
import shutil
import os
import time
import ffmpeg
from pyrogram.types import CallbackQuery
from config import Config
from pyrogram.types import Message
from __init__ import LOGGER

async def MergeVideo(input_file: str, user_id: int, message: Message, format_: str):
    """
    This is for Merging Videos Together!
    :param `input_file`: input.txt file's location.
    :param `user_id`: Pass user_id as integer.
    :param `message`: Pass Editable Message for Showing FFmpeg Progress.
    :param `format_`: Pass File Extension.
    :return: This will return Merged Video File Path
    """
    output_vid = f"downloads/{str(user_id)}/[@yashoswalyo].{format_.lower()}"
    file_generator_command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        input_file,
        "-map",
        "0",
        "-c",
        "copy",
        output_vid,
    ]
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            *file_generator_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except NotImplementedError:
        await message.edit(
            text="Unable to Execute FFmpeg Command! Got `NotImplementedError` ...\n\nPlease run bot in a Linux/Unix Environment."
        )
        await asyncio.sleep(10)
        return None
    await message.edit("Merging Video Now ...\n\nPlease Keep Patience ...")
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    LOGGER.info(e_response)
    LOGGER.info(t_response)
    if os.path.lexists(output_vid):
        return output_vid
    else:
        return None


async def MergeSub(filePath: str, subPath: str, user_id):
    """
    This is for Merging Video + Subtitle Together.

    Parameters:
    - `filePath`: Path to Video file.
    - `subPath`: Path to subtitile file.
    - `user_id`: To get parent directory.

    returns: Merged Video File Path
    """
    LOGGER.info("Generating mux command")
    input_files = ""
    maps = ""
    metadata = ""
    videoData = ffmpeg.probe(filename=filePath)
    videoStreamsData = videoData.get("streams")
    subTrack = 0
    for i in range(len(videoStreamsData)):
        if videoStreamsData[i]["codec_type"] == "subtitle":
            subTrack += 1
    input_files += f"-i '{filePath}' -i '{subPath}' "
    maps += f"-map 1:s "
    metadata += f"-metadata:s:s:{subTrack} title='Track {subTrack+1} - tg@yashoswalyo' "
    subTrack += 1
    LOGGER.info("Sub muxing")
    subprocess.call(
        f"ffmpeg -hide_banner {input_files}-map 0:v:0 -map 0:a:? -map 0:s:? {maps}{metadata}-c:v copy -c:a copy -c:s srt './downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv' ",
        shell=True,
    )
    orgFilePath = shutil.move(
        f"downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv", filePath
    )
    return orgFilePath


def MergeSubNew(filePath: str, subPath: str, user_id, file_list):
    """
    This is for Merging Video + Subtitle(s) Together.

    Parameters:
    - `filePath`: Path to Video file.
    - `subPath`: Path to subtitile file.
    - `user_id`: To get parent directory.
    - `file_list`: List of all input files

    returns: Merged Video File Path
    """
    LOGGER.info("Generating mux command")
    input_files = ""
    maps = ""
    metadata = ""
    videoData = ffmpeg.probe(filename=filePath)
    videoStreamsData = videoData.get("streams")
    subTrack = 0
    for i in range(len(videoStreamsData)):
        if videoStreamsData[i]["codec_type"] == "subtitle":
            subTrack += 1
    for i in file_list:
        input_files += f"-i '{i}' "
    for j in range(1, (len(file_list))):
        maps += f"-map {j}:s "
        metadata += (
            f"-metadata:s:s:{subTrack} title='Track {subTrack+1} - tg@yashoswalyo' "
        )
        subTrack += 1
    LOGGER.info("Sub muxing")
    subprocess.call(
        f"ffmpeg -hide_banner {input_files}-map 0:v:0 -map 0:a:? -map 0:s:? {maps}{metadata}-c:v copy -c:a copy -c:s srt './downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv'",
        shell=True,
    )
    return f"downloads/{str(user_id)}/[@yashoswalyo]_softmuxed_video.mkv"


def MergeAudio(videoPath:str,files_list:list,user_id):
    LOGGER.info("Generating Mux Command")
    inputfiles = ""
    maps = ""
    metadata = ""
    rmDispositions = ""
    videoData = ffmpeg.probe(filename=videoPath)
    videoStreamsData = videoData.get("streams")
    audioTracks = 0
    for i in range(len(videoStreamsData)):
        if videoStreamsData[i]["codec_type"] == "audio":
            rmDispositions += f"-disposition:a:{audioTracks} 0 "
            audioTracks+=1
    for i in files_list:
        inputfiles += f"-i '{i}' "
    for j in range(1,len(files_list)):
        maps += f"-map {j}:a "
    LOGGER.info("Merging files now")
    subprocess.call(
        f"ffmpeg -hide_banner {inputfiles}-map 0:v:0 -map 0:a:? {maps}-map 0:s:? -c:v copy -c:a copy -c:s copy {rmDispositions}-disposition:a:{audioTracks} default './downloads/{str(user_id)}/[@yashoswalyo]_export.mkv'",
        shell=True
    )
    return f"downloads/{str(user_id)}/[@yashoswalyo]_export.mkv"

async def cult_small_video(video_file, output_directory, start_time, end_time, format_):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = (
        output_directory + str(round(time.time())) + "." + format_.lower()
    )
    file_generator_command = [
        "ffmpeg",
        "-i",
        video_file,
        "-ss",
        str(start_time),
        "-to",
        str(end_time),
        "-async",
        "1",
        "-strict",
        "-2",
        out_put_file_name,
    ]
    process = await asyncio.create_subprocess_exec(
        *file_generator_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    LOGGER.info(e_response)
    LOGGER.info(t_response)
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None


async def take_screen_shot(video_file, output_directory, ttl):
    """
    This functions generates custom_thumbnail / Screenshot.

    Parameters:

    - `video_file`: Path to video file.
    - `output_directory`: Path where to save thumbnail
    - `ttl`: Timestamp to generate ss

    returns: This will return path of screenshot
    """
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = os.path.join(output_directory, str(time.time()) + ".jpg")
    if video_file.upper().endswith(
        (
            "MKV",
            "MP4",
            "WEBM",
            "AVI",
            "MOV",
            "OGG",
            "WMV",
            "M4V",
            "TS",
            "MPG",
            "MTS",
            "M2TS",
            "3GP",
        )
    ):
        file_genertor_command = [
            "ffmpeg",
            "-ss",
            str(ttl),
            "-i",
            video_file,
            "-vframes",
            "1",
            out_put_file_name,
        ]
        # width = "90"
        process = await asyncio.create_subprocess_exec(
            *file_genertor_command,
            # stdout must a pipe to be accessible as process.stdout
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
    #
    if os.path.exists(out_put_file_name):
        return out_put_file_name
    else:
        return None
