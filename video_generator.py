from enum import Enum
import json
import datetime
import os
from typing import Literal, Tuple
from moviepy import VideoClip
from reddit_requests import create_post_from_post_id
from comment_based_video import find_comment_post, generate_comments_clip
from story_based_video import find_story_post, generate_story_clip

FINISHED_VIDEO_PATH = "F:/finished_videos/"
threads = 16

with open("config/reddit_threads.json") as file:
    reddit_threads = json.loads(file.read())


def get_already_posted_ids():
    with open("config/already_posted.txt", "r") as file:
        already_posted_ids = file.read().splitlines()
        return already_posted_ids


def add_to_already_posted_ids(new_id: str):
    already_posted_ids = get_already_posted_ids()
    already_posted_ids.append(new_id)
    with open("config/already_posted.txt", "w") as file:
        for id in already_posted_ids:
            file.write(id + "\n")


def generate_story_video(
    resolution: Tuple[int, int],
    timeframe: Literal["day", "week", "month", "year", "all"],
    listing: Literal["controversial", "best", "hot", "new", "random", "rising", "top"],
    approx_video_duration: datetime.timedelta = datetime.timedelta(minutes=5),
    filename: str = "",
):
    if filename == "":
        filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    selected_post = find_story_post(
        timeframe, listing, reddit_threads["story_based"], approx_video_duration
    )
    generate_story_video_by_id(selected_post.post_id, resolution, filename)


def generate_comment_video(
    resolution: Tuple[int, int],
    timeframe: Literal["day", "week", "month", "year", "all"],
    listing: Literal["controversial", "best", "hot", "new", "random", "rising", "top"],
    approx_video_duration: datetime.timedelta = datetime.timedelta(minutes=5),
    filename: str = "",
):
    if filename == "":
        filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    selected_post = find_comment_post(
        timeframe, listing, reddit_threads["comment_based"], approx_video_duration
    )
    generate_comment_video_by_id(selected_post.post_id, resolution, filename)


def generate_story_video_by_id(
    post_id: str,
    resolution: Tuple[int, int],
    filename: str = "",
):
    if filename == "":
        filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    post = create_post_from_post_id(post_id)
    add_to_already_posted_ids(post.post_id)
    print(f'selected post titled "{post.title}"')
    print(f"saving post_id {post.post_id} as selected")

    video: VideoClip = generate_story_clip(post, resolution)
    save_video(video, filename)

    for f in os.listdir("tmp/"):
        if f.startswith(f"{post.post_id}"):
            os.remove(f"tmp/{f}")


def generate_comment_video_by_id(
    post_id: str, resolution: Tuple[int, int], filename: str = ""
):
    if filename == "":
        filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    post = create_post_from_post_id(post_id)
    add_to_already_posted_ids(post.post_id)
    print(f'selected post titled "{post.title}"')
    print(f"saving post_id {post.post_id} as selected")

    video: VideoClip = generate_comments_clip(post, resolution)
    save_video(video, filename)

    for f in os.listdir("tmp/"):
        if f.startswith(f"{post.post_id}"):
            os.remove(f"tmp/{f}")


def save_video(video: VideoClip, filename: str):
    video.write_videofile(
        FINISHED_VIDEO_PATH + filename + ".mp4",
        fps=25,
        threads=threads,
        preset="veryfast",
    )


# generate_story_video((1920, 1080), "month", "top", datetime.timedelta(minutes=5))
generate_comment_video((1920, 1080), "month", "top", datetime.timedelta(minutes=5))


# ps = PostSearch("EntitledPeople", "top", "month")
# for p in ps.posts:
#     print(p.selftext)
#     print(check_if_valid_post(p.post_id, p.title, p.selftext, datetime.timedelta(minutes=5)))
#     input()

# TODO remove urls
# TODO error handling

# TODO mark nsfw
# TODO for some reason "beautiful" gets replaced with "beautoday". maybe only sometimes??
# TODO what to do if post includes the words "reddit"
# TODO ignore post that contain "update" in title
# TODO ignore posts that contain images
# TODO while aligning: if alignment doesnt work: check next words and ignore current one

# title = openaiinterface.create_video_title(p.selftext)
# print(f"Title: {title}")
# summary = openaiinterface.create_video_summary(p.selftext)
# print(f"Intro Summary: {summary}")
