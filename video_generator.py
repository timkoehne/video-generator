import json
from random import randrange

from typing import Literal, Tuple
from moviepy_interface import generate_video
from reddit_requests import Post, PostSearch, create_post_from_post_id


with open("config/reddit_threads.json") as file:
    reddit_threads = json.loads(file.read())


def generate_story_video(
    timeframe: Literal["day", "week", "month", "year", "all"],
    listing: Literal["controversial", "best", "hot", "new", "random", "rising", "top"],
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

    generate_video(selected_post.selftext, (1920, 1080), "my_first_video")


def generate_post_video(post_id: str):
    post = create_post_from_post_id(post_id)
    with open("config/already_posted.txt", "r") as file:
        already_posted_ids = file.read().splitlines()

    already_posted_ids.append(post.post_id)
    with open("config/already_posted.txt", "w") as file:
        for id in already_posted_ids:
            file.write(id + "\n")
    print(f'selected post titled "{post.title}"')
    print(f"saving post_id {post.post_id} as selected")

    generate_video(post.selftext, (1920, 1080), "my_first_video")


# generate_post_video("17pdufg")
generate_story_video("month", "top")
