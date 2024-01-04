from typing import Tuple
from moviepy import CompositeVideoClip, ImageClip, TextClip, VideoClip
from moviepy.video.fx import resize
import numpy as np
from reddit_requests import Post, create_post_from_post_id
from PIL import Image
import urllib.request


sub_reddit_icon_size = 200
bottom_row_margin = 20
bottom_row_image_size = 250
background_color = (255, 255, 255)



def get_concat_v_blank(im1, im2, color=(0, 0, 0)):
    dst = Image.new("RGB", (max(im1.width, im2.width), im1.height + im2.height), color)
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def generate_subreddit_part(
    post: Post, background_color: Tuple[int, int, int]
) -> Image.Image:
    subreddit_image: Image.Image
    with urllib.request.urlopen(post.subreddit_icon_url) as url:
        subreddit_image = Image.open(url)
        if subreddit_image.mode != "RGBA":
            subreddit_image = subreddit_image.convert("RGBA")
    
    
    icon_clip: ImageClip = ImageClip(np.asarray(subreddit_image))
    resize(icon_clip, (sub_reddit_icon_size, sub_reddit_icon_size))

    text_clip: TextClip = TextClip(
        f"r/{post.subreddit}",
        color="red",
        font="Arial-Black",
        font_size=70,
        align="west",
        bg_color="#{:02x}{:02x}{:02x}".format(*background_color),
    )
    text_clip = text_clip.with_position(
        (icon_clip.size[0], (icon_clip.size[1] - text_clip.size[1]) / 2)
    )

    combined_clip = CompositeVideoClip(
        [icon_clip, text_clip],
        bg_color=background_color,
        size=(icon_clip.size[0] + text_clip.size[0], icon_clip.size[1]),
    )
    image = Image.fromarray(combined_clip.get_frame(0))


    return image


def generate_text(
    text: str, resolution: Tuple[int, int], background_color: Tuple[int, int, int]
) -> Image.Image:
    text_clip = TextClip(
        text,
        size=(resolution[0] * 0.8, 0),
        color="red",
        font="Arial-Black",
        font_size=70,
        method="caption",
        align="west",
        bg_color="#{:02x}{:02x}{:02x}".format(*background_color),
    )
    frame = Image.fromarray(text_clip.get_frame(0))
    return frame


def generate_upvotes_part(background_color: Tuple[int, int, int]) -> Image.Image:
    post = create_post_from_post_id("cvb3b6")

    positions: list[Tuple[int, int]] = []
    clips: list[VideoClip] = []

    positions.append((0, 0))
    clips.append(
        resize(ImageClip("config/upvote.png"), (bottom_row_image_size, bottom_row_image_size)).with_position(
            positions[-1]
        )
    )
    positions.append((positions[-1][0] + clips[-1].size[0] + bottom_row_margin, 0))
    clips.append(
        TextClip(
            str(post.upvotes),
            color="DarkGray",
            font="Arial-Black",
            font_size=70,
            align="center",
            bg_color="#{:02x}{:02x}{:02x}".format(*background_color),
        ).with_position(positions[-1])
    )

    positions.append((positions[-1][0] + clips[-1].size[0] + 3 * bottom_row_margin, 0))
    clips.append(
        resize(
            ImageClip("config/speech_bubble.png"), (bottom_row_image_size, bottom_row_image_size)
        ).with_position(positions[-1])
    )

    positions.append((positions[-1][0] + clips[-1].size[0] + bottom_row_margin, 0))
    clips.append(
        TextClip(
            str(post.num_comments),
            color="DarkGray",
            font="Arial-Black",
            font_size=70,
            align="center",
            bg_color="#{:02x}{:02x}{:02x}".format(*background_color),
        ).with_position(positions[-1])
    )

    max_height: int = max(clips, key=lambda clip: clip.size[1]).size[1]
    # clips = [clip.with_position() for clip in clips]
    for i in range(0, len(clips)):
        positions[i] = (positions[i][0], (max_height - clips[i].size[1]) / 2)
        clips[i] = clips[i].with_position(positions[i])
    final_size = (positions[-1][0] + clips[-1].size[0], max_height)

    res = CompositeVideoClip(clips, size=final_size, bg_color=background_color)
    return Image.fromarray(res.get_frame(0))


def generate_thumbnail_with_text(post: Post, resolution: Tuple[int, int]):

    subreddit_part = generate_subreddit_part(post, background_color)
    text_part = generate_text(post.title, resolution, background_color)
    bottom_row = generate_upvotes_part(background_color)



    image = get_concat_v_blank(subreddit_part, text_part, color=background_color)
    image = get_concat_v_blank(image, bottom_row, color=background_color)
    image.show()

    return image
