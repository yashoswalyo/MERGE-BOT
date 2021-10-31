import asyncio
import os
import time
from config import Config
from pyrogram.types import Message


async def MergeVideo(input_file: str, user_id: int, message: Message, format_: str):
	"""
	This is for Merging Videos Together!
	:param input_file: input.txt file's location.
	:param user_id: Pass user_id as integer.
	:param message: Pass Editable Message for Showing FFmpeg Progress.
	:param format_: Pass File Extension.
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
		output_vid
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
	print(e_response)
	print(t_response)
	if os.path.lexists(output_vid):
		return output_vid
	else:
		return None


async def cult_small_video(video_file, output_directory, start_time, end_time, format_):
	# https://stackoverflow.com/a/13891070/4723940
	out_put_file_name = output_directory + str(round(time.time())) + "." + format_.lower()
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
		out_put_file_name
	]
	process = await asyncio.create_subprocess_exec(
		*file_generator_command,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.PIPE,
	)
	stdout, stderr = await process.communicate()
	e_response = stderr.decode().strip()
	t_response = stdout.decode().strip()
	print(e_response)
	print(t_response)
	if os.path.lexists(out_put_file_name):
		return out_put_file_name
	else:
		return None


async def generate_screen_shots(video_file, output_directory, no_of_photos, duration):
	images = list()
	ttl_step = duration // no_of_photos
	current_ttl = ttl_step
	for looper in range(no_of_photos):
		await asyncio.sleep(1)
		video_thumbnail = f"{output_directory}/{str(time.time())}.jpg"
		file_generator_command = [
			"ffmpeg",
			"-ss",
			str(round(current_ttl)),
			"-i",
			video_file,
			"-vframes",
			"1",
			video_thumbnail
		]
		process = await asyncio.create_subprocess_exec(
			*file_generator_command,
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.PIPE,
		)
		stdout, stderr = await process.communicate()
		e_response = stderr.decode().strip()
		t_response = stdout.decode().strip()
		print(e_response)
		print(t_response)
		current_ttl += ttl_step
		images.append(video_thumbnail)
	return images
