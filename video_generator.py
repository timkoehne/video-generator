from enum import Enum
import json
import datetime
from typing import Literal, Tuple
from moviepy import VideoClip
from moviepy_interface import generate_comments_clip, generate_story_clip
from reddit_requests import create_post_from_post_id, find_post


class VideoType:
    def __init__(self, name: str, generator_function) -> None:
        self.name = name
        self.generator_function = generator_function


class VideoTypeEnum(Enum):
    STORY = VideoType("story_based", generate_story_clip)
    COMMENT = VideoType("comment_based", generate_comments_clip)


FINISHED_VIDEO_PATH = "C:/Users/Tim/Desktop/finished_videos/"
threads = 16

with open("config/reddit_threads.json") as file:
    reddit_threads = json.loads(file.read())


def generate_video(
    video_type: VideoTypeEnum,
    resolution: Tuple[int, int],
    timeframe: Literal["day", "week", "month", "year", "all"],
    listing: Literal["controversial", "best", "hot", "new", "random", "rising", "top"],
    filename: str = datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
):
    with open("config/already_posted.txt", "r") as file:
        already_posted_ids = file.read().splitlines()
    selected_post = find_post(timeframe, listing, reddit_threads[video_type.value.name])
    already_posted_ids.append(selected_post.post_id)
    with open("config/already_posted.txt", "w") as file:
        for id in already_posted_ids:
            file.write(id + "\n")
    print(f'selected post titled "{selected_post.title}"')
    print(f"saving post_id {selected_post.post_id} as selected")

    video: VideoClip = video_type.value.generator_function(selected_post, resolution)

    video.write_videofile(
        FINISHED_VIDEO_PATH + filename + ".mp4",
        fps=25,
        threads=threads,
        preset="veryfast",
    )


def generate_post_video(
    post_id: str, filename: str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
):
    post = create_post_from_post_id(post_id)
    with open("config/already_posted.txt", "r") as file:
        already_posted_ids = file.read().splitlines()

    already_posted_ids.append(post.post_id)
    with open("config/already_posted.txt", "w") as file:
        for id in already_posted_ids:
            file.write(id + "\n")
    print(f'selected post titled "{post.title}"')
    print(f"saving post_id {post.post_id} as selected")

    generate_story_clip(post, (1920, 1080), filename)


# generate_video(VideoTypeEnum.STORY, "month", "top")
generate_video(VideoTypeEnum.COMMENT, (1080, 1920), "month", "top")
