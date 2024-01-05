import sys
from typing import Tuple
from moviepy import CompositeVideoClip, ImageClip, TextClip, VideoClip
from moviepy.video.fx import resize
import numpy as np
from configuration import Configuration
from reddit_requests import Post, create_post_from_post_id
from PIL import Image
import urllib.request

config = Configuration()


def hex_to_rgb(hex: str) -> Tuple[int, int, int]:
    if hex.startswith("#"):
        hex = hex[1:]
    return tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore


def change_image_color(
    img: Image.Image, new_color: Tuple[int, int, int]
) -> Image.Image:
    image = np.array(img)

    rgb = image[..., :3]
    alpha = image[..., 3]

    non_transparent_pixels = alpha != 0
    # new_color = np.array(new_color)

    rgb[non_transparent_pixels] = new_color
    modified_image_array = np.concatenate((rgb, alpha[..., np.newaxis]), axis=-1)
    modified_image = Image.fromarray(modified_image_array.astype(np.uint8))
    return modified_image


def generate_subreddit_part(post: Post) -> Image.Image:
    subreddit_image: Image.Image | None = None

    print(f"trying to request subreddit icon")
    for i in range(0, 5):
        try:
            with urllib.request.urlopen(post.subreddit_icon_url) as url:
                subreddit_image = Image.open(url)
                if subreddit_image.mode != "RGBA":
                    subreddit_image = subreddit_image.convert("RGBA")
                    subreddit_image = subreddit_image.resize(
                        (
                            config.thumbnail_subreddit_icon_size,
                            config.thumbnail_subreddit_icon_size,
                        )
                    )
                    break
        except Exception:
            print(f"retrying attempt {i}")

    if subreddit_image == None:
        print("could not find subreddit icon. using default reddit logo.")
        subreddit_image = Image.open(config.thumbnail_default_subreddit_icon)

    icon_clip: ImageClip = ImageClip(np.asarray(subreddit_image))

    text_clip: TextClip = TextClip(
        f"r/{post.subreddit}",
        color=config.thumbnail_subreddit_text_color,
        font=config.thumbnail_subreddit_text_font,
        font_size=config.thumbnail_subreddit_text_size,
        align="west",
        bg_color=config.thumbnail_background_color,
        # bg_color="#{:02x}{:02x}{:02x}".format(*background_color),
    )
    text_clip = text_clip.with_position(
        (
            icon_clip.size[0] + config.thumbnail_element_margin,
            (icon_clip.size[1] - text_clip.size[1]) / 2,
        )
    )

    combined_clip = CompositeVideoClip(
        [icon_clip, text_clip],
        bg_color=hex_to_rgb(config.thumbnail_background_color),
        size=(
            icon_clip.size[0] + text_clip.size[0] + config.thumbnail_element_margin,
            icon_clip.size[1],
        ),
    )
    image = Image.fromarray(combined_clip.get_frame(0))

    return image


def generate_text_part(text: str, resolution: Tuple[int, int]) -> Image.Image:
    text_clip = TextClip(
        text,
        size=(resolution[0] * (1 - 2 * config.thumbnail_side_offset), 0),
        color=config.thumbnail_main_text_color,
        font=config.thumbnail_main_text_font,
        font_size=config.thumbnail_main_text_size,
        method="caption",
        align="west",
        bg_color=config.thumbnail_background_color,
    )
    frame = Image.fromarray(text_clip.get_frame(0))
    return frame


def generate_upvotes_part(post: Post) -> Image.Image:
    positions: list[Tuple[int, int]] = []
    clips: list[VideoClip] = []

    upvote_img = Image.open(config.thumbnail_upvotes_icon)
    upvote_img = change_image_color(
        upvote_img, hex_to_rgb(config.thumbnail_like_text_color)
    )
    upvote_image_arr = np.array(upvote_img)

    comments_img = Image.open(config.thumbnail_comments_icon)
    comments_img = change_image_color(
        comments_img, hex_to_rgb(config.thumbnail_like_text_color)
    )
    comments_img_arr = np.array(comments_img)

    positions.append((0, 0))
    clips.append(
        resize(
            ImageClip(upvote_image_arr),
            (config.thumbnail_like_icon_size, config.thumbnail_like_icon_size),
        ).with_position(positions[-1])
    )
    positions.append(
        (positions[-1][0] + clips[-1].size[0] + config.thumbnail_element_margin, 0)
    )
    clips.append(
        TextClip(
            str(post.upvotes),
            color=config.thumbnail_like_text_color,
            font=config.thumbnail_like_text_font,
            font_size=config.thumbnail_like_text_size,
            align="center",
            bg_color=config.thumbnail_background_color,
        ).with_position(positions[-1])
    )

    positions.append(
        (positions[-1][0] + clips[-1].size[0] + 3 * config.thumbnail_element_margin, 0)
    )
    clips.append(
        resize(
            ImageClip(comments_img_arr),
            (config.thumbnail_like_icon_size, config.thumbnail_like_icon_size),
        ).with_position(positions[-1])
    )

    positions.append(
        (positions[-1][0] + clips[-1].size[0] + config.thumbnail_element_margin, 0)
    )
    clips.append(
        TextClip(
            str(post.num_comments),
            color=config.thumbnail_like_text_color,
            font=config.thumbnail_like_text_font,
            font_size=config.thumbnail_like_text_size,
            align="center",
            bg_color=config.thumbnail_background_color,
        ).with_position(positions[-1])
    )

    max_height: int = max(clips, key=lambda clip: clip.size[1]).size[1]
    # clips = [clip.with_position() for clip in clips]
    for i in range(0, len(clips)):
        positions[i] = (positions[i][0], (max_height - clips[i].size[1]) / 2)
        clips[i] = clips[i].with_position(positions[i])
    final_size = (positions[-1][0] + clips[-1].size[0], max_height)

    res = CompositeVideoClip(
        clips, size=final_size, bg_color=hex_to_rgb(config.thumbnail_background_color)
    )
    return Image.fromarray(res.get_frame(0))


def generate_thumbnail_with_text(post: Post, resolution: Tuple[int, int]):
    subreddit_part = generate_subreddit_part(post)
    text_part = generate_text_part(post.title, resolution)
    upvotes_part = generate_upvotes_part(post)

    image = Image.new("RGB", resolution, config.thumbnail_background_color)

    text_part_pos = (
        int(config.thumbnail_side_offset * resolution[0]),
        int(0.5 * resolution[1] - text_part.height / 2),
    )
    subreddit_part_pos = (
        int(config.thumbnail_side_offset * resolution[0]),
        text_part_pos[1] - subreddit_part.height,
    )
    upvotes_part_pos = (
        int(config.thumbnail_side_offset * resolution[0]),
        text_part_pos[1] + text_part.height + config.thumbnail_element_margin,
    )

    image.paste(text_part, text_part_pos)
    image.paste(subreddit_part, subreddit_part_pos)
    image.paste(upvotes_part, upvotes_part_pos)
    
    return image
