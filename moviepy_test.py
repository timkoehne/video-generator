from math import floor
from random import randrange
from moviepy.video.fx import resize, crop
from moviepy import *
from typing import Tuple
from openai_test import OpenAiTest
import os


BACKGROUND_VIDEO_PATH = "background_videos/"
POSSIBLE_FILE_ENDINGS = (".mp4", ".webm", ".mkv", ".ogv", ".mpeg", ".avi", ".mov")


def generate_text_clip(text: str, size: Tuple[float, float]):
    # good fonts:
    # arial-black
    # cooper-black
    # franklin-gothic-heavy

    return TextClip(
        text=text,
        method="caption",
        color="white",
        font="Arial-Black",
        font_size=70,
        stroke_color="black",
        stroke_width=5,
        size=(size[0], size[1]),
        align="center",
    )


def generate_text_list(text: str):
    words: list[str] = text.split(" ")
    text_list: list[str] = []

    num_words = []

    while len(words) > 0:  # split into chunks of different lengths
        length = min(randrange(6, 9), len(words))
        num_words.append(length)
        words = words[length:]

    if num_words[-1] < 3:  # is the last text too short? add it to the previous one
        num_words[-2] += num_words[-1]
        num_words.pop()
    sum = 0
    words = text.split(" ")
    for num in num_words:
        text_list.append(" ".join(words[sum : sum + num]))
        sum += num

    return text_list


def generate_combined_text_clip(
    text: str, time_per_char: float, size: Tuple[float, float]
):
    text_clips = []
    text_sections = generate_text_list(text)
    print(f"splitting text into {len(text_sections)} clips")
    for section in text_sections:
        text_clip: TextClip = generate_text_clip(section, size)

        duration = len(section) * time_per_char
        # print(f"\"{section}\" is played for {duration} seconds")

        text_clip = text_clip.with_duration(duration)
        text_clip = text_clip.with_position("center")
        text_clips.append(text_clip)
    return concatenate_videoclips(text_clips).with_position("center")


def select_background_video(min_length: int, max_attempts: int = 10) -> VideoFileClip:
    clip: VideoClip = VideoFileClip("background_videos/Minecraft_Parkour.webm")

    possible_videos: list[str] = os.listdir(BACKGROUND_VIDEO_PATH)
    possible_videos = list(
        filter(lambda x: x.endswith(POSSIBLE_FILE_ENDINGS), possible_videos)
    )

    selected_file = possible_videos[randrange(0, len(possible_videos))]
    clip = VideoFileClip(BACKGROUND_VIDEO_PATH + selected_file)
    print(f"selected {selected_file} as background video")

    if min_length > clip.duration:
        if max_attempts > 0:
            print("retrying for background video since it isn't long enough")
            clip = select_background_video(min_length, max_attempts - 1)
        else:
            raise Exception("No suitable background video found")
    return clip


def crop_to_center(clip: VideoClip, new_aspect_ratio: float):
    x1 = (clip.size[0] - (clip.size[1] * new_aspect_ratio)) // 2
    x2 = (clip.size[0] + (clip.size[1] * new_aspect_ratio)) // 2
    y1 = 0
    y2 = clip.size[1]

    return clip.fx(crop, x1=x1, x2=x2, y1=y1, y2=y2)


def generate_video(text: str, resolution: Tuple[int, int], filename: str) -> None:
    print("SKIPPING GENERATING AUDIO")
    # openaitest = OpenAiTest()
    # print("generating audio")
    # openaitest.generate_audio(text, "audio.mp3.tmp")
    audio_clip: AudioClip = AudioFileClip("audio.mp3.tmp")
    print(f"the video will be {audio_clip.duration}s long")

    time_per_char: float = audio_clip.duration / len(text)
    print("average time per char: " + str(time_per_char) + "s")

    text_box_size = (resolution[0] * 0.8, 0)
    combined_text_clip = generate_combined_text_clip(text, time_per_char, text_box_size)

    backgroundVideo: VideoClip = select_background_video(combined_text_clip.duration)
    backgroundVideo = crop_to_center(backgroundVideo, resolution[0] / resolution[1])
    backgroundVideo = backgroundVideo.fx(resize, resolution)

    start_time = randrange(
        0, floor(backgroundVideo.duration - combined_text_clip.duration)
    )
    end_time = start_time + combined_text_clip.duration

    print(
        f"using background video time between {start_time}s and {end_time}s out of {backgroundVideo.duration}s"
    )

    backgroundVideo = backgroundVideo.subclip(start_time, end_time)
    result = CompositeVideoClip(
        [backgroundVideo, combined_text_clip]
    )

    result = result.with_audio(audio_clip)
    result.write_videofile(f"finished_videos/{filename}.mp4", fps=25)


text = """
I am a 20 year old female but the story I am about to tell happened when I was around 7 years old. So to give a little backstory, from the ages of 4-12, my family and I lived on a heavily wooded 14 acre property in the south. 
"""

generate_video(text, (1920, 1080), "my_first_video")
generate_video(text, (1080, 1920), "my_first_short")
