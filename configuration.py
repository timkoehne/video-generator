import json
from typing import Literal


class Configuration:
    def __init__(self) -> None:
        with open("config/configuration.json") as file:
            config = json.loads(file.read())

        self.output_dir = config["output_dir"]
        self.background_videos_dir = config["background_videos_dir"]
        self.tolerated_duration_offset = config["tolerated_duration_offset"]
        self.intro_header: str = config["intro_header"]
        self.intro_prompt: str = config["intro_prompt"]
        self.outro_prompt: str = config["outro_prompt"]
        self.video_title_prompt: str = config["video_title_prompt"]
        self.background_video_volume: float = config["background_video_volume"]
        self.thumbnail_image_dir: str = config["thumbnail_image_dir"]
        self.thumbnail_text_width_percent: float = config["thumbnail_text_width_percent"]
        self.thumbnail_allowed_overlap: float = config["thumbnail_allowed_overlap"]
        self.thumbnail_edge_width: int = config["thumbnail_edge_width"]
        self.thumbnail_person_aspect_ratio_min: float = config["thumbnail_person_aspect_ratio_min"]
        self.thumbnail_person_aspect_ratio_max: float = config["thumbnail_person_aspect_ratio_max"]
        

        self.init_text_clips(config)
        self.init_text_wall(config)

        self.init_openai(config)
        self.init_moviepy(config)

    def init_text_wall(self, config):
        self.text_wall_font: str = config["text_wall_font"]
        self.text_wall_font_color: str = config["text_wall_font_color"]
        self.text_wall_font_size: int = config["text_wall_font_size"]
        self.text_wall_font_stroke_width: int = config["text_wall_font_stroke_width"]
        self.text_wall_font_stroke_color: str = config["text_wall_font_stroke_color"]

    def init_text_clips(self, config):
        self.text_clips_font: str = config["text_clips_font"]
        self.text_clips_font_color: str = config["text_clips_font_color"]
        self.text_clips_font_size: int = config["text_clips_font_size"]
        self.text_clips_font_stroke_width: int = config["text_clips_font_stroke_width"]
        self.text_clips_font_stroke_color: str = config["text_clips_font_stroke_color"]

    def init_moviepy(self, config):
        self.video_fps: int = config["video_fps"]
        self.write_video_preset: str = config["write_video_preset"]
        self.num_threads: int = config["num_threads"]

    def init_openai(self, config):
        with open("config/secrets.json", "r") as file:
            secrets = json.loads(file.read())
            self.openai_api_key = secrets["openai_api_key"]

        self.audio_api: Literal["openai"] = config["audio_api"]
        if self.audio_api == "openai":
            self.audio_model: Literal["tts-1", "tts-1-hd"] = config["audio_model"]
            self.audio_voice: Literal[
                "alloy", "echo", "fable", "onyx", "nova", "shimmer"
            ] = config["audio_voice"]
