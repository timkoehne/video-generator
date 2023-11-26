from typing import Tuple

from moviepy import *
from video_utils import crop_to_center_and_resize, select_background_video
from openai_interface import OpenAiInterface
from reddit_requests import Comment, Post
from text_processing import split_text_to_max_x_chars


def calculate_font_size(text: str) -> Tuple[list[str], list[int]]:
    text_parts: list[str] = split_text_to_max_x_chars(text, 550)
    font_sizes: list[int] = []

    for part in text_parts:
        if len(part) > 400:
            font_sizes.append(45)
        elif len(part) > 200:
            font_sizes.append(50)
        else:
            font_sizes.append(70)

    return (text_parts, font_sizes)


def generate_comment_intro(title: str, resolution: Tuple[int, int]) -> VideoClip:
    openaiinterface = OpenAiInterface()
    openaiinterface.generate_mp3(title, f"tmp/audio-intro.mp3")

    intro_clip: VideoClip = TextClip(
        title,
        size=(resolution[0] * 0.8, 0),
        color="white",
        font="Arial-Black",
        font_size=70,
        method="caption",
        stroke_color="black",
        stroke_width=3,
        align="center",
    )
    audio_clip = AudioFileClip(f"tmp/audio-intro.mp3")
    intro_clip = intro_clip.with_duration(audio_clip.duration + 1.5)
    intro_clip = intro_clip.with_audio(audio_clip)
    return intro_clip


def generate_single_comment_clip(
    text_parts: list[str],
    font_sizes: list[int],
    resolution: Tuple[int, int],
    index: int,
):
    openaiinterface = OpenAiInterface()
    comment_clip_parts: list[VideoClip] = []

    for i, part in enumerate(text_parts):
        openaiinterface.generate_mp3(part, f"tmp/audio-{index}-part-{i}.mp3")
        # clip_parts.append()
        clip_part: VideoClip = TextClip(
            part,
            size=(resolution[0] * 0.8, 0),
            color="white",
            font="Arial-Black",
            font_size=font_sizes[i],
            method="caption",
            stroke_color="black",
            stroke_width=3,
            align="center",
        )

        audio_clip = AudioFileClip(f"tmp/audio-{index}-part-{i}.mp3")
        clip_part = clip_part.with_duration(audio_clip.duration + 1)
        clip_part = clip_part.with_audio(audio_clip)
        comment_clip_parts.append(clip_part)

    comment_clip = concatenate_videoclips(comment_clip_parts)
    return comment_clip


def generate_comments_clip(post: Post, resolution: Tuple[int, int]) -> VideoClip:
    text_clips: list[VideoClip] = []
    intro: VideoClip = generate_comment_intro(post.title, resolution)

    comments: list[Comment] = post.get_good_comments()
    print(f"There are {len(comments)} good comments")

    for index, comment in enumerate(comments):
        print(comment)

        text_parts, font_sizes = calculate_font_size(comment.body)
        if len(text_parts) > 1:
            print(f"Splitting Comment into {len(text_parts)} parts")

        comment_clip = generate_single_comment_clip(
            text_parts, font_sizes, resolution, index
        )
        text_clips.append(comment_clip)
    combined_text_video: VideoClip = concatenate_videoclips(text_clips)
    combined_text_video = concatenate_videoclips([intro, combined_text_video])
    combined_text_video = combined_text_video.with_position("center")

    background_video: VideoClip = select_background_video(combined_text_video.duration)
    background_video = crop_to_center_and_resize(background_video, resolution)
    result = CompositeVideoClip([background_video, combined_text_video])
    return result
