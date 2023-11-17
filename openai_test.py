import json
from pathlib import Path
from typing import Literal
from moviepy import AudioClip, AudioFileClip, concatenate_audioclips
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

    def split_text_to_max_4096_chars(self, text: str) -> list[str]:
        if len(text) > 4096:
            first_part = text[0:4096]
            period_index = first_part.rindex(".")
            first_part = text[0:period_index]
            return [first_part] + self.split_text_to_max_4096_chars(text[period_index:])
        else:
            return [text]


    def generate_mp3(self, 
                       text: str, 
                       filepath: str,
                       model: str = "tts-1", 
                       voice: Literal['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'] = "fable"):
        
        filename = filepath[:filepath.index(".")]
        ext = filepath[filepath.index(".")+1:]
        
        text_segments: list[str] = self.split_text_to_max_4096_chars(text)
        
        if len(text_segments) < 2:
            response = self.client.audio.speech.create(
                    input=text,
                    model="tts-1",
                    voice=voice, 
                    response_format="mp3"
            )
            response.stream_to_file(filename + ".mp3")
        else:
            print(f"audio is too long for openai. requesting {len(text_segments)} audio files")
        
            audio_files: list[AudioClip] = []
            for index, text_segment in enumerate(text_segments):
                print(f"requesting audio file {index}")
                
                response = self.client.audio.speech.create(
                    input=text_segment,
                    model="tts-1",
                    voice=voice,
                )
                
                tmp_file_name: str = filename + "-" + str(index) + ".mp3"
                response.stream_to_file(tmp_file_name)
                audio_files.append(AudioFileClip(tmp_file_name))
            
            print(f"combining audio files")
            combined_audio: AudioClip = concatenate_audioclips(audio_files)
            combined_audio.write_audiofile(filepath)
    

