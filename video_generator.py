from enum import Enum
import json
import datetime
import os
from random import randrange
import sys
from typing import Literal, Tuple
from moviepy import CompositeVideoClip, TextClip, VideoClip
from configuration import Configuration
from openai_interface import OpenAiInterface
from reddit_requests import Post, PostSearch, create_post_from_post_id
from comment_based_video import find_comment_post, generate_comments_clip
from story_based_video import find_story_post, generate_story_clip
from thumbnail_with_text import generate_thumbnail_with_text
from video_utils import (
    check_if_valid_post,
    crop_to_center_and_resize,
    is_between_durations,
    select_background_video,
)

config = Configuration()

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
):
    selected_post = find_story_post(
        timeframe, listing, reddit_threads["story_based"], approx_video_duration
    )
    generate_story_video_by_id(selected_post.post_id, resolution)


def generate_comment_video(
    resolution: Tuple[int, int],
    timeframe: Literal["day", "week", "month", "year", "all"],
    listing: Literal["controversial", "best", "hot", "new", "random", "rising", "top"],
    approx_video_duration: datetime.timedelta = datetime.timedelta(minutes=5),
):
    selected_post = find_comment_post(
        timeframe, listing, reddit_threads["comment_based"], approx_video_duration
    )
    generate_comment_video_by_id(selected_post.post_id, resolution)


def generate_story_video_by_id(
    post_id: str,
    resolution: Tuple[int, int],
    generate_intro: bool = True,
    generate_outro: bool = True,
):
    post = create_post_from_post_id(post_id)
    add_to_already_posted_ids(post.post_id)
    print(f'selected post titled "{post.title}"')
    print(f"saving post_id {post.post_id} as selected")

    video: VideoClip = generate_story_clip(
        post, resolution, "english", add_intro=generate_intro, add_outro=generate_outro
    )

    background_video: VideoClip
    background_video_credit: str
    background_video, background_video_credit = select_background_video(video.duration)
    background_video = crop_to_center_and_resize(background_video, resolution)
    video = CompositeVideoClip([background_video, video])

    if not os.path.exists(config.output_dir + post.post_id):
        os.mkdir(config.output_dir + post.post_id)

    save_video(video, post)

    generate_and_save_description_and_tags(post, background_video_credit, "story")
    generate_and_save_title(post)

    thumbnail = generate_thumbnail_with_text(post, resolution)
    thumbnail.save(f"{config.output_dir + post.post_id}/thumbnail.jpg")

    for f in os.listdir("tmp/"):
        if f.startswith(f"{post.post_id}"):
            os.remove(f"tmp/{f}")


def generate_comment_video_by_id(
    post_id: str,
    resolution: Tuple[int, int],
    generate_intro: bool = True,
    generate_outro: bool = True,
):
    post = create_post_from_post_id(post_id)
    add_to_already_posted_ids(post.post_id)
    print(f'selected post titled "{post.title}"')
    print(f"saving post_id {post.post_id} as selected")

    video: VideoClip = generate_comments_clip(
        post, resolution, generate_intro, generate_outro
    )

    background_video: VideoClip
    background_video_credit: str
    background_video, background_video_credit = select_background_video(video.duration)
    background_video = crop_to_center_and_resize(background_video, resolution)
    video = CompositeVideoClip([background_video, video])

    if not os.path.exists(config.output_dir + post.post_id):
        os.mkdir(config.output_dir + post.post_id)

    save_video(video, post)

    generate_and_save_description_and_tags(post, background_video_credit, "comment")
    generate_and_save_title(post)
    thumbnail = generate_thumbnail_with_text(post, resolution)
    thumbnail.save(f"{config.output_dir + post.post_id}/thumbnail.jpg")

    for f in os.listdir("tmp/"):
        if f.startswith(f"{post.post_id}"):
            os.remove(f"tmp/{f}")
            pass


def generate_and_save_title(post: Post):
    openaiinterface = OpenAiInterface(system_prompt=config.video_title_prompt)
    prompt = post.title + "\n" + post.selftext
    
    for _ in range(0, 5):
        response = openaiinterface.generate_text_with_context(
            prompt
        )
        response = f"{response} | r/{post.subreddit} Reddit Stories"
        print(f"title is {response}")
        if len(response) > 0 and len(response) < 100:
            print("title too long. trying to shorten...")
            prompt = "shorter"
            break
        else:
            raise Exception("could not generate a video title")

    with open(config.output_dir + post.post_id + "/title.txt", "w") as file:
        file.write(response) #type: ignore


def generate_and_save_description_and_tags(
    post: Post, background_credit: str, type_of_video: Literal["comment", "story"]
):
    if type_of_video == "story":
        reddit_credit = f"This story was posted by {post.author} to r/{post.subreddit}. Available at:\n{post.url}\n"
    elif type_of_video == "comment":
        reddit_credit = f"These comments were posted in response to {post.author}'s post on r/{post.subreddit}. Available at:\n{post.url}\n"

    
    tags = ["reddit", "redditstories", post.subreddit]
    with open(config.output_dir + post.post_id + "/tags.txt", "w") as file:
        file.write(",".join(tags))
    hashtags = " ".join(["#"+tag for tag in tags])

    with open(config.background_videos_dir + "channel_urls.json", "r") as file:
        credit_url = json.loads(file.read())[background_credit]
        background_credit = f"The background gameplay is by {background_credit}. Check them out at:\n{credit_url}\n"

    openai_disclaimer = f'The audio is AI-generated from {config.audio_api}\'s text-to-speech model "{config.audio_model}" with the voice "{config.audio_voice}".'

    description = reddit_credit + "\n" + background_credit + "\n" + openai_disclaimer + "\n\n" + hashtags

    with open(config.output_dir + post.post_id + "/description.txt", "w") as file:
        file.write(description)


def save_video(video: VideoClip, post: Post):
    video.write_videofile(
        config.output_dir + post.post_id + "/video.mp4",
        fps=config.video_fps,
        threads=config.num_threads,
        preset=config.write_video_preset,
    )


# generate_story_video((1920, 1080), "all", "top", datetime.timedelta(minutes=5))
# generate_comment_video((1920, 1080), "all", "top", datetime.timedelta(minutes=5))


# with open("config/reddit_threads.json", "r") as file:
#     for subreddit in json.loads(file.read())["story_based"]:
#         ps = PostSearch(subreddit, "top", "all")
#         for post in ps.posts:
#             if check_if_valid_post(post.post_id, post.title, post.selftext):
#                 if is_between_durations(post.selftext, datetime.timedelta(minutes=4), datetime.timedelta(minutes=25)):
#                     print(f"{post.post_id} is within specified time")
#                     generate_story_video_by_id(post.post_id, (1920, 1080))
#                     sys.exit(0)


# TODO remove urls
# TODO error handling

# TODO for some reason "beautiful" gets replaced with "beautoday". maybe only sometimes??
# TODO ignore posts that contain images
# TODO what to do with configuration text_wall_font_size? its dependent on text length

# TODO audio and text sometimes desync for a short time noticable in joz1c5.
# probably also caused overlapping audio with the outro

# TODO subreddit name can overflow out of the image if its long enough. probably only relevant on vertical video



# # my usage 
# for i in range(0, 10):
#     post = find_story_post(
#         "all",
#         "top",
#         reddit_threads["story_based"],
#         # min_duration=datetime.timedelta(seconds=20),
#         # max_duration=datetime.timedelta(seconds=60),
#         min_duration=datetime.timedelta(minutes=4),
#         max_duration=datetime.timedelta(minutes=25),
#     )

    
#     try:
#         generate_story_video_by_id(
#             # post.post_id, (1080, 1920), generate_intro=False, generate_outro=False
#             post.post_id, (1920, 1080), generate_intro=True, generate_outro=True,
#         )
#     except Exception as e:
#         print(e)
#         pass

