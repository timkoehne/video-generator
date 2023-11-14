import json
from pathlib import Path
from typing import Literal
from openai import OpenAI
from PIL import Image
from io import BytesIO
import base64


class OpenAiTest:
    def __init__(self) -> None:
        with open("secrets.json", "r") as file:
            secrets = json.loads(file.read())
            openai_api_key = secrets["openai_api_key"]

        self.client = OpenAI(api_key=openai_api_key)

    def generate_image(self, 
                       prompt: str, 
                       filenames: list[str], 
                       model: str = "dall-e-2", 
                       size: Literal['256x256', '512x512', '1024x1024', '1792x1024', '1024x1792'] = "1024x1024", 
                       quality: Literal['standard', 'hd'] = "standard"):
        response = self.client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=len(filenames),
            response_format="b64_json",
        )
        image_url = response.data[0].url
        
        image_data_list = []
        for index, image in enumerate(response.data):
          data = image.model_dump()["b64_json"]
          im = Image.open(BytesIO(base64.b64decode(data)))
          im.save(filenames[index])
  

        print(image_url)

    def generate_audio(self, 
                       text: str, 
                       filename: str,
                       model: str = "tts-1", 
                       voice: Literal['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'] = "fable"):
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        response.stream_to_file(filename)
