# video-generator
Generate Youtube-Videos about stories or comments from Reddit with background gameplay footage, text overlays and text-to-speech from OpenAI.

This projects created all videos on this [Youtube Channel](https://www.youtube.com/@Reddit-StoryScrolls/videos) automatically.


# Requirements
- Conda Environment with a recent Python3 (tested on 3.12.3)
- Montreal Forced Aligner CLI
    - ```conda install conda install -c conda-forge montreal-forced-aligner```
    - Aswell as the corresponding models
        - ```mfa models download acoustic english_us_arpa```
        - ```mfa models download dictionary english_us_arpa```
- All Python packages can be installed with ```pip install -r requirements.txt```
    - except [moviepy v2.0.0.dev2](https://github.com/Zulko/moviepy) which needs to be installed manually by cloning the project and running with ```pip install .\moviepy\ .\moviepy\[optional] .\moviepy\[doc]```


# Features
- Find posts from Reddit based on subreddit, popularity, time, estimated tts-duration
    - Clean-up posts by removing edits, tldrs, updates, disclaimers aswell as useless one-liners about spelling, formatting, reposts, account-history
```python
# create a post from reddit id
post_0 = create_post_from_post_id("fjnawl")

# find a story post
post_1 = find_story_post(
    "all",
    "top",
    subreddit_list=["AmItheAsshole", "confessions"],
    min_duration=datetime.timedelta(minutes=4),
    max_duration=datetime.timedelta(minutes=25))

# find a comment post
post_2 = find_comment_post(
    "all",
    "top", 
    subreddit_list=["AskReddit", "NoStupidQuestions"],
    approx_video_duration=datetime.timedelta(minutes=5))

```


- Create a video based on a post using:
    - OpenAI to generate text-to-speech audio
    - ImageMagick to write the text a few words at a time onto the screen
    - Montreal-Forced-Aligner to align text with the audio
    - Select gameplay video as background from library
    - Write youtube title, description, tags
    - generate a thumbnail

```python
#generate a video based on the story of the post
generate_story_video_by_id(
    post_1.post_id, (1920, 1080), generate_intro=True, generate_outro=True,
)

#
generate_comment_video_by_id(
    post_2.post_id, (1920, 1080), generate_intro=True, generate_outro=True,
)
```

# Configuration
You need to specify your OpenAI API-Key in ``secrets.json`` according to ``secrets template.json``.



You can configure alot of settings in ``config/configuration.json``. The most important ones:
- ``output_dir`` to specify where your finished videos are saved. Each finished video will have its own directory containing the video file, the thumbnail aswell as text documents for the video description, tags and title.
- ``background_videos_dir`` to specify the folder containing background videos. This folder should have subfolders for each Youtube-Channel where your background video is from. There should also be a file called ``channel_urls.json`` that has urls to the background videos creators Youtube channels.


You can also specify font settings, some moviepy settings aswell as OpenAI prompts and models here.