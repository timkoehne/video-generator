from argparse import FileType
import json
from pathlib import Path
import time
from typing import Literal
from moviepy import AudioClip, AudioFileClip, concatenate_audioclips
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64
from configuration import Configuration

from text_processing import split_text_to_max_x_chars


class OpenAiInterface:
    def __init__(self) -> None:
        self.config = Configuration()
        self.client = OpenAI(api_key=self.config.openai_api_key)

    def generate_image(
        self,
        prompt: str,
        filename: str,
        model: str = "dall-e-2",
        size: Literal[
            "256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"
        ] = "1024x1024",
        quality: Literal["standard", "hd"] = "standard",
    ):
        response = self.client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
            response_format="b64_json",
        )

        name, file_type = filename.split(".")

        for index, image in enumerate(response.data):
            data = image.model_dump()["b64_json"]
            im = Image.open(BytesIO(base64.b64decode(data)))
            im.save(f"{name}-{index}.{file_type}")

    def edit_image(
        self, image_path: str, mask_path: str, prompt: str, output_path: str
    ):
        response = self.client.images.edit(
            image=open(image_path, "rb"),
            mask=open(mask_path, "rb"),
            prompt=prompt,
            model="dall-e-2",
            response_format="b64_json",
        )

        name, file_type = output_path.split(".")
        for index, image in enumerate(response.data):
            data = image.model_dump()["b64_json"]
            im = Image.open(BytesIO(base64.b64decode(data)))
            im.save(f"{name}-{index}.{file_type}")

    def generate_mp3(
        self,
        text: str,
        filepath: str,
    ):
        
        
        filename = filepath[: filepath.index(".")]
        ext = filepath[filepath.index(".") + 1 :]

        text_segments: list[str] = split_text_to_max_x_chars(text, 4096)

        if len(text_segments) < 2:
            response = self.client.audio.speech.create(
                input=text, model=self.config.audio_model, voice=self.config.audio_voice, response_format="mp3"
            )
            response.stream_to_file(filename + ".mp3")
        else:
            print(
                f"audio is too long for openai. requesting {len(text_segments)} audio files"
            )

            audio_files: list[AudioClip] = []
            for index, text_segment in enumerate(text_segments):
                print(f"requesting audio file {index}")

                response = self.client.audio.speech.create(
                    input=text_segment,
                    model=self.config.audio_model,
                    voice=self.config.audio_voice,
                )

                tmp_file_name: str = filename + "-" + str(index) + ".mp3"
                response.stream_to_file(tmp_file_name)
                audio_files.append(AudioFileClip(tmp_file_name))

            print(f"combining audio files")
            combined_audio: AudioClip = concatenate_audioclips(audio_files)
            combined_audio.write_audiofile(filepath)

    def generate_text_without_context(
        self, system_prompt: str, text: str, tries=5
    ) -> str:
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": text},
            ],
            model="gpt-4-1106-preview",
        )

        if isinstance(chat_completion.choices[0].message.content, str):
            return chat_completion.choices[0].message.content
        else:
            print(f"openai text generation error. retries left: {tries}")
            if tries > 0:
                time.sleep(3)
                return self.generate_text_without_context(
                    system_prompt, text, tries - 1
                )
            else:
                raise Exception("openai text generation failed")
