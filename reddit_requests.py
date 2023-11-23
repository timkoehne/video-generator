from typing import Tuple
import requests
import json
import emoji
import re

useragent = "yourbot"


class PostSearch:
    def __init__(self, subreddit: str, listing: str, timeframe: str) -> None:
        try:
            print(f"Trying to access {listing} posts of {timeframe} from {subreddit}")
            base_url = f"https://www.reddit.com/r/{subreddit}/{listing}.json?t={timeframe}"  # &limit={limit}
            print(base_url)
            request = requests.get(base_url, headers={"User-agent": useragent})
            posts_listing = request.json()

            self.posts: list[Post] = []
            for post in get_parameter(posts_listing, "children"):
                self.posts.append(Post(post))
        except:
            print("an error occured while searching for posts")


class Post:
    def __str__(self) -> str:
        return (
            self.author
            + ' created the post: "'
            + self.title
            + '" which has '
            + str(self.score)
            + " score"
        )

    def load_comments(self, listing):
        try:
            print(f"Trying to access comments of post {self.post_id}")
            base_url = f"https://www.reddit.com/{self.post_id}/.json?sort={listing}"
            request = requests.get(base_url, headers={"User-agent": "yourbot"})
            comments = request.json()[1]["data"]["children"]

            for comment in comments:
                self.comments.append(Comment(comment))
        except Exception as e:
            print(
                f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"
            )
            print("an error cccured while searching for comments")

    def __init__(self, post) -> None:
        self.subreddit: str = get_parameter(post, "subreddit")
        self.title: str = get_parameter(post, "title")
        self.author: str = get_parameter(post, "author")
        self.selftext: str = get_parameter(post, "selftext")
        self.post_id: str = get_parameter(post, "id")
        self.gilded: int = int(get_parameter(post, "gilded"))
        self.upvotes: int = int(get_parameter(post, "ups"))
        self.downvotes: int = int(get_parameter(post, "downs"))
        self.score: int = int(get_parameter(post, "score"))
        self.url: str = get_parameter(post, "url")
        self.comments: list[Comment] = []

        self.selftext = text_cleanup(self.selftext)

    def get_good_comments(self, score_threshold: int = 100):
        if len(self.comments) == 0:
            self.load_comments("top")

        print(f"there are {len(self.comments)} comments")
        for index, comment in enumerate(self.comments):
            chain_score = calc_chain_score(comment)

            print(
                f"{index}, : Comment from {comment.author} has {comment.score} score. This comment chain has a combined {chain_score}"
            )

        return list(
            filter(
                lambda comment: calc_chain_score(comment) > score_threshold,
                self.comments,
            )
        )


class Comment:
    def __str__(self) -> str:
        return f'{self.author} wrote: "{self.body}"'

    def load_comment_chain(self, depth=0):
        chain: list[Comment] = []
        chain.append(self)
        if depth > 1 and len(self.replies) > 0:
            chain += self.replies[0].load_comment_chain(depth - 1)
        return chain

    def __init__(self, comment) -> None:
        self.author: str = get_parameter(comment, "author")
        self.body: str = get_parameter(comment, "body")
        self.replies: list[Comment] = handle_replies(get_parameter(comment, "replies"))
        self.upvotes: int = int(get_parameter(comment, "ups"))
        self.downvotes: int = int(get_parameter(comment, "downs"))
        self.score: int = int(get_parameter(comment, "score"))
        self.gilded: int = int(get_parameter(comment, "gilded"))
        
        self.body = text_cleanup(self.body)


def create_post_from_post_id(post_id: str) -> Post:
    base_url = f"https://www.reddit.com/{post_id}.json"
    print(base_url)
    request = requests.get(base_url, headers={"User-agent": useragent})
    post = request.json()[0]
    post = get_parameter(post, "children")[0]
    # print(post)
    return Post(post)


def handle_replies(replies) -> list[Comment]:
    ret = []

    if isinstance(replies, str):
        pass
    else:
        for child in replies["data"]["children"]:
            if "kind" in child and child["kind"] == "more":
                # TODO handle loading more comments
                # print(replies)
                pass
            else:
                ret.append(Comment(child))

    return ret


def get_parameter(data, parameter):
    if "kind" in data and data["kind"] == "more":
        return "0"

    if "data" in data:
        data = data["data"]

    if parameter in data:
        return data[parameter]

    raise Exception("Unknown Parameter")


def calc_chain_score(comment: Comment, skip_first: bool = True) -> int:
    sum = comment.score

    for reply in comment.replies:
        sum += calc_chain_score(reply, False)

    return sum


def text_cleanup(text: str) -> str:
    to_remove = ["\nedit", "*edit", "\ntldr", "\ntl;dr", "update:"]
    for phrase in to_remove:
        if phrase in text.lower():
            edit_position = text.lower().index(phrase)
            if edit_position > len(text) * 0.4:
                print(f"removing {phrase.strip()}")
                text = text[0:edit_position]

    text = " ".join(text.split())
    text = text.replace(" , ", ", ")
    text = text.replace(" . ", ". ")
    text = text.replace("“", '"')
    text = emoji.replace_emoji(text, "")

    for match in re.findall('[a-zA-Z]+"[a-zA-Z]+', text):
        replace_with = " ".join(match.split('"'))
        text = text.replace(match, replace_with)
        print(f"replacing {match} with {replace_with}")

    for match in re.findall("[a-zA-Z]\(", text):
        replace_with = " (".join(match.split("("))
        text = text.replace(match, replace_with)
        print(f"replacing {match} with {replace_with}")

    for match in re.findall("\)[a-zA-Z]", text):
        replace_with = ") ".join(match.split(")"))
        text = text.replace(match, replace_with)
        print(f"replacing {match} with {replace_with}")

    # markdown links
    for match in re.findall("(\[([^\]]+)\]\((\S+(?=\)))\))", text):
        replace_with = match[1]
        print(f"replacing {match[0]} with {replace_with}")
        text = text.replace(match[0], match[1])

    # for match in  re.findall('[a-zA-Z]+-[a-zA-Z]+', text):
    #     replace_with = " ".join(match.split("-"))
    #     text = text.replace(match, replace_with)
    #     print(f"replacing {match} with {replace_with}")

    with open("config/replace_in_text.txt") as file:
        for line in file.readlines():
            line = line.strip("\n")
            replace_from, replace_to = line.split(",")
            # print(f"replacing \"{replace_from}\" with \"{replace_to}\"")
            text = text.replace(replace_from, replace_to)

    # print(self.post_id)
    print(text)
    return text