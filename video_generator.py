import json
from random import randrange
import datetime
import re

from typing import Literal, Tuple

from moviepy import AudioFileClip, CompositeVideoClip, TextClip, VideoClip, concatenate_videoclips
from moviepy_interface import generate_comments_clip, generate_video, crop_to_center_and_resize, select_background_video
from openai_interface import OpenAiInterface
from reddit_requests import Post, PostSearch, Comment, create_post_from_post_id
from moviepy.video.fx import resize, crop


with open("config/reddit_threads.json") as file:
    reddit_threads = json.loads(file.read())


def generate_story_video(
    timeframe: Literal["day", "week", "month", "year", "all"],
    listing: Literal["controversial", "best", "hot", "new", "random", "rising", "top"],
    filename: str = datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
):
    with open("config/already_posted.txt", "r") as file:
        already_posted_ids = file.read().splitlines()

    maxAttempts = 50
    while True:
        subreddit = reddit_threads["story_based"][
            randrange(0, len(reddit_threads["story_based"]))
        ]
        search = PostSearch(subreddit, listing, timeframe)
        selected_post = search.posts[randrange(0, len(search.posts))]
        # TODO check if this is a valid post: post body length

        if not selected_post.post_id in already_posted_ids:
            break
        else:
            maxAttempts -= 1
            if maxAttempts <= 0:
                raise Exception(f"No valid post found in {maxAttempts} attempts.")

    already_posted_ids.append(selected_post.post_id)
    with open("config/already_posted.txt", "w") as file:
        for id in already_posted_ids:
            file.write(id + "\n")
    print(f'selected post titled "{selected_post.title}"')
    print(f"saving post_id {selected_post.post_id} as selected")

    generate_video(selected_post.selftext, (1080, 1920), filename)


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

    generate_video(post.selftext, (1920, 1080), filename)


def generate_comment_video(
    post_id: str, filename: str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
):
    selected_post = create_post_from_post_id(post_id)

    comments: list[Comment] = selected_post.get_good_comments()
    print(f"There are {len(comments)} good comments")


    resolution = (1920, 1080)
    
    #TODO determine font size based on text length
    #TODO maybe make two screen if text is too long
    #TODO cleanup tmp folder
    #TODO background video audio level
    #TODO background video audio in story videos missing
    
    
    # for comment in comments[0].load_comment_chain(3):
    # print(comment)
    
    comments_text_video: VideoClip = generate_comments_clip(comments[:3], resolution)
    background_video: VideoClip = select_background_video(comments_text_video.duration)
    background_video = crop_to_center_and_resize(background_video, resolution)
    comments_text_video = CompositeVideoClip([background_video, comments_text_video])
    comments_text_video.write_videofile(filename + ".mp4", fps=25)
    
    

# generate_post_video("17j7yoo")
# generate_story_video("month", "top")
generate_comment_video("180rjhn")


