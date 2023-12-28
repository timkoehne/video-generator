import os
import random
import sys
from typing import Tuple
import cv2
from moviepy import *
from PIL import Image
import numpy as np

from configuration import Configuration
from db_access import DB_Controller

config = Configuration()


class Rectangle:
    def __init__(
        self,
        top_left: Tuple[float, float],
        top_right: Tuple[float, float],
        bottom_left: Tuple[float, float],
        bottom_right: Tuple[float, float],
    ) -> None:
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right
        pass

    def width(self):
        return self.top_right[0] - self.top_left[0]

    def height(self):
        return self.bottom_left[1] - self.top_left[1]

    def aspect_ratio(self):
        return self.width() / self.height()


def get_bordered_pil_image(path: str, edge_size: int):
    src = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    alpha = cv2.split(src)[3]

    # scale so it is roughly the same at every resolution
    edge_size = int(edge_size * len(alpha[0]) / 1000)

    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(alpha, kernel, iterations=edge_size)
    output_image = cv2.merge((dilated, dilated, dilated, dilated))
    pil_image = Image.fromarray(output_image)

    return pil_image


def find_thumbnail_person(bounds: Rectangle, keywords: list[str]) -> Image.Image:
    db_controller = DB_Controller("database.db")
    candidates = db_controller.find_images_with_tags(keywords)
    random.shuffle(candidates)
    for candidate in candidates:
        person = Image.open(os.path.join(config.thumbnail_image_dir, candidate))
        aspect_ratio = person.width / person.height

        lower_bound = (
            bounds.aspect_ratio()
            - config.thumbnail_person_aspect_ratio_min * bounds.aspect_ratio()
        )
        upper_bound = (
            bounds.aspect_ratio()
            + config.thumbnail_person_aspect_ratio_max * bounds.aspect_ratio()
        )
        # print(f"lowerbounds has aspect_ratio of {lower_bound}")
        # print(f"upperbounds has aspect_ratio of {upper_bound}")
        # print(f"person has aspect_ratio of {aspect_ratio}")

        if lower_bound < aspect_ratio < upper_bound:
            candidate = candidates[random.randrange(0, len(candidates))]
            print(f"selected {candidate}")
            background = Image.new("RGBA", (person.width, person.height), (0, 0, 0, 0))

            # background.paste((0, 0, 0, 255), mask=bordered_person)
            background.paste(person, (0, 0), mask=person)
            # background.show()

            return background

    raise Exception("No suitable thumbnail person found")


def generate_thumbnail_text_clip(title: str, resolution: Tuple[int, int]):
    text_max_width = int(resolution[0] * config.thumbnail_text_width_percent)

    text = title.split(" ")
    texts = []
    for index in range(0, len(text), 2):
        if index == len(text) - 1:
            texts.append(text[index])
        else:
            texts.append(text[index] + " " + text[index + 1])

    text = "\n".join(texts).strip()

    txt_clip = TextClip(
        text=text,
        method="caption",
        color=config.text_clips_font_color,
        # font=config.text_clips_font,
        font=config.text_clips_font,
        font_size=100,
        stroke_color=config.text_clips_font_stroke_color,
        stroke_width=6,
        size=(text_max_width, resolution[1]),
        align="west",
    ).with_position((25, 0))

    return txt_clip


def generate_thumbnail_background_clip(background_clip: VideoClip):
    screenshot_time = random.random() * background_clip.duration
    img_clip = ImageClip(background_clip.get_frame(screenshot_time))
    return img_clip


def calculate_person_max_bounds(resolution: Tuple[int, int]):
    allowed_overlap = int(config.thumbnail_allowed_overlap * resolution[0])
    top_left = (
        (config.thumbnail_text_width_percent * resolution[0]) - allowed_overlap,
        0,
    )
    top_right = (resolution[0], 0)
    bottom_left = (
        (config.thumbnail_text_width_percent * resolution[0]) - allowed_overlap,
        resolution[1],
    )
    bottom_right = (resolution[0], resolution[1])

    return Rectangle(top_left, top_right, bottom_left, bottom_right)


def thumbnail_add_person(
    thumbnail: Image.Image, person_max_bounds: Rectangle, person: Image.Image
):
    # scale = min(
    #     person_max_bounds.width() / person.width,
    #     person_max_bounds.height() / person.height,
    # )
    scale = person_max_bounds.height() / person.height
    width = int(person.width * scale)
    height = int(person.height * scale)

    person = person.resize((width, height))

    remaining_width = person_max_bounds.width() - width
    remaining_height = person_max_bounds.height() - height

    thumbnail.paste(
        person,
        (
            int(person_max_bounds.top_left[0]) + int(1 / 2 * remaining_width),
            thumbnail.size[1] - person.size[1],
        ),
        person,
    )

    return thumbnail


def generate_thumbnail(title: str, background_clip: VideoClip, keywords: list[str]):
    resolution = (1920, 1080)
    txt_clip = generate_thumbnail_text_clip(title, resolution)
    thumbnail_background = generate_thumbnail_background_clip(background_clip)
    clip = CompositeVideoClip([thumbnail_background, txt_clip])
    thumbnail = Image.fromarray(clip.get_frame(0))

    person_max_bounds = calculate_person_max_bounds(resolution)
    print(
        f"person box dimensions {person_max_bounds.width()}x{person_max_bounds.height()}"
    )

    person: Image.Image = find_thumbnail_person(person_max_bounds, keywords)

    thumbnail = thumbnail_add_person(thumbnail, person_max_bounds, person)
    thumbnail.show()
