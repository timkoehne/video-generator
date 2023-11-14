from math import floor
from random import randrange
from moviepy.video.fx import resize, crop
from moviepy import *
from typing import Tuple
from openai_test import OpenAiTest
import os
import subprocess
import textgrid


BACKGROUND_VIDEO_PATH = "f:/background_videos/"
POSSIBLE_FILE_ENDINGS = (".mp4", ".webm", ".mkv", ".ogv", ".mpeg", ".avi", ".mov")

mfa_dictionary_names = {
    "english": ["english_us_arpa", "english_us_arpa"],
    "german": ["german_mfa", "german_mfa"],
}


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
    words: list[str] = [x.strip() for x in text.split(" ")]
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
    words = [x.strip() for x in text.split(" ")]
    for num in num_words:
        text_list.append(" ".join(words[sum : sum + num]))
        sum += num

    return text_list


def generate_combined_text_clip(
    text: str, text_box_size: Tuple[float, float], textgrid_filename: str
):
    text_clips = []
    text_sections = generate_text_list(text)
    print(f"splitting text into {len(text_sections)} clips")
    timestamps = parseTextgrid(textgrid_filename, text_sections)

    for section in timestamps:
        text_clip: TextClip = generate_text_clip(section[0], text_box_size)

        duration = section[2] - section[1]
        print(f"{section} is played for {duration:.2f} seconds")

        text_clip = text_clip.with_duration(duration)
        text_clip = text_clip.with_position("center")
        text_clips.append(text_clip)
    return concatenate_videoclips(text_clips).with_position("center")


def select_background_video(min_length: int, max_attempts: int = 10) -> VideoFileClip:

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


def generate_video(
    text: str, 
    resolution: Tuple[int, int], 
    filename: str, 
    language: str = "english"
) -> None:
    # print("SKIPPING GENERATING AUDIO")
    openaitest = OpenAiTest()
    print("generating audio")
    openaitest.generate_audio(text, "tmp/audio.aac")
    audio_clip: AudioClip = AudioFileClip("tmp/audio.aac")
    
    audio_clip.write_audiofile("tmp/audio.wav")
    print(f"the video will be {audio_clip.duration}s long")
    with open("tmp/audio.txt", "w", encoding='utf-8') as file:
        file.write(text)
    align_audio_and_text("tmp/audio.wav", "tmp/audio.txt", language)

    text_box_size = (resolution[0] * 0.8, 0)
    combined_text_clip = generate_combined_text_clip(
        text, text_box_size, "tmp/audio.TextGrid"
    )

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
    result = CompositeVideoClip([backgroundVideo, combined_text_clip])

    result = result.with_audio(audio_clip)
    result.write_videofile(f"finished_videos/{filename}.mp4", fps=25)


def align_audio_and_text(audio_filename: str, text_filename: str, language: str):
    dictionary_name, acoustic_model_name = mfa_dictionary_names[language]

    subprocess.run(
        [
            "mfa",
            "align_one",
            audio_filename,
            text_filename,
            dictionary_name,
            acoustic_model_name,
            "tmp/",
        ]
    )


def parseTextgrid(filename, text_segments: list[str]):
    tg = textgrid.TextGrid.fromFile(filename)

    # tg[0] is the ist of words
    # remove pauses and stuff
    filtered_tg = filter(lambda x: not x.mark.startswith("<"), tg[0])
    filtered_tg = list(filtered_tg)

    timestamps: list[Tuple[str, float, float]] = []

    i = 0
    for segment in text_segments:
        segment = segment.strip()
        first = True
        start: float = 0.0
        end: float = 0.0
        for word in segment.split(" "):
            if first:
                start = filtered_tg[i].minTime
                first = False
            i += 1
        end = filtered_tg[i - 1].maxTime
        timestamps.append((segment, start, end))
    return timestamps


text = """I am a 20 year old female but the story I am about to tell happened when I was around 7 years old. So to give a little backstory, from the ages of 4-12, my family and I lived on a heavily wooded 14 acre property in the south. """


# generate_video(text, (1920, 1080), "my_first_video")
generate_video(text, (1080, 1920), "my_first_short")