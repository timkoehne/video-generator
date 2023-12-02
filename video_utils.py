from math import floor
from pathlib import Path
from random import randint, randrange
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
    start_time = randint(0, floor(clip.duration - min_length))
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


def generate_intro(post: Post, resolution: Tuple[int, int]) -> VideoClip:
    openaiinterface = OpenAiInterface()
    openaiinterface.generate_mp3(post.title, f"tmp/{post.post_id}-audio-intro.mp3")

    intro_clip: VideoClip = TextClip(
        post.title,
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
    intro_clip = intro_clip.with_duration(audio_clip.duration + 1.25)
    intro_clip = intro_clip.with_audio(audio_clip)
    
    print(f"Creating intro from title with duration {intro_clip.duration}s")
    
    return intro_clip