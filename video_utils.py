from datetime import timedelta
from math import floor
from pathlib import Path
from random import randint, randrange
import random
from moviepy.video.fx import resize, crop
from moviepy.audio.fx import multiply_volume
from moviepy import *
from typing import Tuple
from openai_interface import OpenAiInterface

from reddit_requests import Post


BACKGROUND_VIDEO_PATH = "f:/background_videos/"
POSSIBLE_FILE_ENDINGS = (".mp4", ".webm", ".mkv", ".ogv", ".mpeg", ".avi", ".mov")

CHARS_PER_SECOND = (10000 / 10.5) / 60
DURATION_OFFSET_PERCENT = 0.25


def select_background_video(min_length: int, max_attempts: int = 10) -> VideoClip:
    possible_videos = [
        p.resolve()
        for p in Path(BACKGROUND_VIDEO_PATH).glob("**/*")
        if p.suffix in POSSIBLE_FILE_ENDINGS
    ]

    selected_file = possible_videos[randrange(0, len(possible_videos))]
    clip: VideoClip = VideoFileClip(selected_file)
    print(f"selected {selected_file} as background video")

    if min_length > clip.duration:
        if max_attempts > 0:
            print(
                f"retrying for background video since it isn't long enough: Attempts left: {max_attempts}"
            )
            clip = select_background_video(min_length, max_attempts - 1)
        else:
            raise Exception("No suitable background video found")

    print(
        f"clip duration {clip.duration} and min_length {min_length} combined: {floor(clip.duration - min_length)}"
    )
    start_time = random.random() * (clip.duration - min_length)
    end_time = start_time + min_length

    print(
        f"using background video time between {start_time}s and {end_time}s out of {clip.duration}s"
    )

    clip = clip.subclip(start_time, end_time)
    clip = clip.afx(multiply_volume, 0.1)

    return clip


def crop_to_center_and_resize(clip: VideoClip, to_resolution: Tuple[int, int]):
    new_aspect_ratio: float = to_resolution[0] / to_resolution[1]
    x1 = (clip.size[0] - (clip.size[1] * new_aspect_ratio)) // 2
    x2 = (clip.size[0] + (clip.size[1] * new_aspect_ratio)) // 2
    y1 = 0
    y2 = clip.size[1]

    clip = clip.fx(crop, x1=x1, x2=x2, y1=y1, y2=y2)
    clip = clip.fx(resize, to_resolution)
    return clip


def generate_intro_clip(post: Post, resolution: Tuple[int, int]) -> VideoClip:
    openaiinterface = OpenAiInterface()
    intro_text = openaiinterface.generate_text_without_context(
        "write an intro for a youtube video in two sentences. Today's topic is this story that someone posted. Do not mention a channel name.",
        post.title + "\n" + post.selftext,
    )
    openaiinterface.generate_mp3(intro_text, f"tmp/{post.post_id}-audio-intro.mp3")

    intro_clip: VideoClip = TextClip(
        "Today's Topic:\n" + post.title,
        size=(resolution[0] * 0.8, 0),
        color="white",
        font="Arial-Black",
        font_size=70,
        method="caption",
        stroke_color="black",
        stroke_width=3,
        align="center",
    )
    audio_clip = AudioFileClip(f"tmp/{post.post_id}-audio-intro.mp3")
    intro_clip = intro_clip.with_duration(audio_clip.duration + 1)
    intro_clip = intro_clip.with_audio(audio_clip)

    print(f"Created intro with duration {intro_clip.duration}s")

    return intro_clip


def generate_outro_clip(post: Post, resolution: Tuple[int, int]) -> VideoClip:
    openaiinterface = OpenAiInterface()
    outro_text = openaiinterface.generate_text_without_context(
        "write an outro for a youtube video in two sentences. Today's topic was this story that someone posted. Do not mention a channel name.",
        post.title + "\n" + post.selftext,
    )
    openaiinterface.generate_mp3(outro_text, f"tmp/{post.post_id}-audio-outro.mp3")

    outro_clip: VideoClip = TextClip(" ")
    audio_clip = AudioFileClip(f"tmp/{post.post_id}-audio-outro.mp3")
    outro_clip = outro_clip.with_duration(audio_clip.duration + 1)
    outro_clip = outro_clip.with_audio(audio_clip)

    print(f"Created outro with duration {outro_clip.duration}s")
    return outro_clip


def create_video_title(self, text: str) -> str:
    openaiinterface = OpenAiInterface()

    response = openaiinterface.generate_text_without_context(
        "write a youtube video title based on this", text
    )
    return response


def check_if_valid_post(
    post_id: str, post_title: str, text_to_check: str, approx_video_duration: timedelta
) -> bool:
    with open("config/already_posted.txt", "r") as file:
        already_posted_ids = file.read().splitlines()
    if post_id in already_posted_ids:
        print(f"Post {post_id} has already been posted")
        return False

    filter_word_in_title = ["update:", "(update)"]
    for word in filter_word_in_title:
        if word in post_title.lower():
            print(f"Post {post_id} is an update")
            return False

    if post_title.lower().startswith("update "):
        print(f"Post {post_id} is an update")
        return False

    expected_duration_seconds = approx_video_duration.total_seconds()
    duration_lower_bound = expected_duration_seconds - (
        expected_duration_seconds * DURATION_OFFSET_PERCENT
    )
    duration_upper_bound = expected_duration_seconds + (
        expected_duration_seconds * DURATION_OFFSET_PERCENT
    )
    # print(f"looking for a post that takes between {duration_lower_bound} and {duration_upper_bound} seconds")
    post_duration = len(text_to_check) / CHARS_PER_SECOND
    if duration_lower_bound > post_duration or post_duration > duration_upper_bound:
        print(
            f"Post {post_id} duration {post_duration} is not within {DURATION_OFFSET_PERCENT*100}% of {expected_duration_seconds}"
        )
        return False

    print(f"Post {post_id} is valid")
    return True
