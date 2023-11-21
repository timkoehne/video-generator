from math import floor
from pathlib import Path
from random import randrange
from moviepy.video.fx import resize, crop
from moviepy import *
from typing import Tuple
from openai_interface import OpenAiInterface
import subprocess
import textgrid
import string


class Timestamp:
    def __init__(self, text: str, from_time: float, to_time: float) -> None:
        self.text = text
        self.from_time = from_time
        self.to_time = to_time


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
    text: str, resolution: Tuple[float, float], textgrid_filename: str
):
    text_clips: list[TextClip] = []
    text_sections: list[str] = generate_text_list(text)
    print(f"splitting text into {len(text_sections)} clips")
    timestamps: list[Timestamp] = parse_textgrid(textgrid_filename, text_sections)

    text_box_size = (resolution[0] * 0.8, 0)

    for section in timestamps:
        text_clip: TextClip = generate_text_clip(section.text, text_box_size)
        text_clip = text_clip.with_start(section.from_time)
        text_clip = text_clip.with_end(section.to_time)
        print(
            f"{section.text} is played from {section.from_time:.2f} to {section.to_time:.2f} seconds"
        )
        text_clip = text_clip.with_position("center")
        text_clips.append(text_clip)
    return CompositeVideoClip(text_clips, resolution).with_position("center")


def select_background_video(min_length: int, max_attempts: int = 10) -> VideoFileClip:
    possible_videos = [
        p.resolve()
        for p in Path(BACKGROUND_VIDEO_PATH).glob("**/*")
        if p.suffix in POSSIBLE_FILE_ENDINGS
    ]

    selected_file = possible_videos[randrange(0, len(possible_videos))]
    clip = VideoFileClip(selected_file)
    print(f"selected {selected_file} as background video")

    if min_length > clip.duration:
        if max_attempts > 0:
            print("retrying for background video since it isn't long enough")
            clip = select_background_video(min_length, max_attempts - 1)
        else:
            raise Exception("No suitable background video found")

    start_time = randrange(0, floor(clip.duration - min_length))
    end_time = start_time + min_length

    print(
        f"using background video time between {start_time}s and {end_time}s out of {clip.duration}s"
    )

    clip = clip.subclip(start_time, end_time)

    return clip


def crop_to_center(clip: VideoClip, new_aspect_ratio: float):
    x1 = (clip.size[0] - (clip.size[1] * new_aspect_ratio)) // 2
    x2 = (clip.size[0] + (clip.size[1] * new_aspect_ratio)) // 2
    y1 = 0
    y2 = clip.size[1]

    return clip.fx(crop, x1=x1, x2=x2, y1=y1, y2=y2)


def generate_video(
    text: str, resolution: Tuple[int, int], filename: str, language: str = "english"
) -> None:
    # print("SKIPPING GENERATING AUDIO")
    openaitest = OpenAiInterface()
    print("generating audio")
    openaitest.generate_mp3(text, "tmp/audio.mp3")

    audio_clip: AudioClip = AudioFileClip("tmp/audio.mp3")
    audio_clip.write_audiofile("tmp/audio.wav")
    print(f"the video will be {audio_clip.duration}s long")

    with open("tmp/audio.txt", "w", encoding="utf-8") as file:
        exclude = set(string.punctuation)
        file.write("".join(char for char in text if char not in exclude))

    align_audio_and_text("tmp/", language)

    combined_text_clip: VideoClip = generate_combined_text_clip(
        text, resolution, "tmp/audio.TextGrid"
    )

    backgroundVideo: VideoClip = select_background_video(
        combined_text_clip.duration + 0.75
    )
    backgroundVideo = crop_to_center(backgroundVideo, resolution[0] / resolution[1])
    backgroundVideo = backgroundVideo.fx(resize, resolution)

    result: VideoClip = CompositeVideoClip([backgroundVideo, combined_text_clip])

    result = result.with_audio(audio_clip)
    result.write_videofile(f"finished_videos/{filename}.mp4", fps=25)


def align_audio_and_text(audio_and_text_dir: str, language: str):
    dictionary_name, acoustic_model_name = mfa_dictionary_names[language]

    subprocess.run(
        [
            "mfa",
            "align",
            audio_and_text_dir,
            dictionary_name,
            acoustic_model_name,
            "tmp/",
            "--clean",
            "--single_speaker",
        ]
    )


def parse_textgrid(filename, text_segments: list[str]):
    tg = textgrid.TextGrid.fromFile(filename)
    # tg[0] is the list of words
    # filter to remove pauses
    filtered_tg = filter(lambda x: not x.mark == "", tg[0])
    filtered_tg = list(filtered_tg)
    print(f"filtered_tg is {len(filtered_tg)} long ")

    words = " ".join(text_segments).split()
    for i in range(min(len(filtered_tg), len(words))):
        print(f"{filtered_tg[i]} - {words[i]}")

    timestamps: list[Timestamp] = []
    for index, segment in enumerate(text_segments[:-1]):
        from_index = sum(len(s.split()) for s in text_segments[:index])
        to_index = sum(len(s.split()) for s in text_segments[:index + 1])
        start_time = filtered_tg[from_index].minTime
        end_time = filtered_tg[to_index].maxTime
        # print(f"from_index {from_index}={words[from_index]}, to_index {to_index}={words[to_index]}")
        timestamps.append(Timestamp(segment, start_time, end_time))

    last_timestamp_start_time = filtered_tg[sum(len(s.split()) for s in text_segments[:-1])].minTime
    last_timestamp_end_time = filtered_tg[-1].maxTime
    timestamps.append(Timestamp(text_segments[-1], last_timestamp_start_time, last_timestamp_end_time))

    # making sure the timestamps dont overlap
    for index in range(1, len(timestamps)):
        if timestamps[index].from_time < timestamps[index - 1].to_time:
            # print(f"changing to_time of index {index-1} from {timestamps[index - 1].to_time} to {timestamps[index].from_time-0.01}")
            timestamps[index - 1].to_time = timestamps[index].from_time - 0.01

    return timestamps