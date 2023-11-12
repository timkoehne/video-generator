import requests
import json

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

    def searchComments(self, listing):
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
        self.post_id: str = get_parameter(post, "id")
        self.gilded: int = int(get_parameter(post, "gilded"))
        self.upvotes: int = int(get_parameter(post, "ups"))
        self.downvotes: int = int(get_parameter(post, "downs"))
        self.score: int = int(get_parameter(post, "score"))
        self.url: str = get_parameter(post, "url")
        self.comments: list[Comment] = []


class Comment:
    def __str__(self) -> str:
        return f'{self.author} wrote: "{self.body}"'

    def load_comment_chain(self, depth=0):
        chain: list[Comment] = []
        chain.append(self)
        if depth > 1 and len(self.replies) > 0:
            chain += self.replies[0].load_comment_chain(depth-1)
        return chain
        


    def __init__(self, comment) -> None:
        self.author: str = get_parameter(comment, "author")
        self.body: str = get_parameter(comment, "body")
        self.replies: list[Comment] = handle_replies(get_parameter(comment, "replies"))
        self.upvotes: int = int(get_parameter(comment, "ups"))
        self.downvotes: int = int(get_parameter(comment, "downs"))
        self.score: int = int(get_parameter(comment, "score"))
        self.gilded: int = int(get_parameter(comment, "gilded"))


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


def calc_replies_score(comment):  # only pay attention to direct children
    sum = 0
    if "kind" in comment and comment["kind"] == "t1":
        if comment["data"]["replies"] == "":
            sum += int(get_parameter(comment, "score"))
        else:
            replies = comment["data"]["replies"]["data"]["children"]
            for reply in replies:
                reply_score = int(get_parameter(reply, "score"))
                # print("comment by", get_parameter(reply, "author"), "has", reply_score, "reply_score")
                sum += reply_score
    return sum


def test(comment, score_threshold):  # only pay attention to direct children
    ret = []
    if "kind" in comment and comment["kind"] == "t1":
        if comment["data"]["replies"] == "":
            if int(get_parameter(comment, "score")) > score_threshold:
                ret.append(comment)
        else:
            replies = comment["data"]["replies"]["data"]["children"]
            if int(get_parameter(comment, "score")) > score_threshold:
                ret.append(comment)
            for reply in replies:
                ret += test(reply, score_threshold)
    return ret


def get_good_comments(comments):
    score_threshold = 100

    for index, comment in enumerate(comments):
        replies_comment_score = calc_replies_score(comment)

        a = test(comment, score_threshold)
        with open("a.json", "a") as file:
            file.write(json.dumps(a))

        print(
            index,
            ": Comment from",
            get_parameter(comment, "author"),
            "has",
            get_parameter(comment, "score"),
            "score. replies have a combined",
            replies_comment_score,
            "comment score",
        )

    return list(
        filter(
            lambda comment: int(get_parameter(comment, "score")) > score_threshold,
            comments,
        )
    )


subreddit = "showerthoughts"
# limit = 100
timeframe = "month"  # hour, day, week, month, year, all
listing = "top"  # controversial, best, hot, new, random, rising, top

search = PostSearch(subreddit, listing, timeframe)
# for post in search.posts:
#     print(post)


search.posts[1].searchComments("top")
comments = search.posts[1].comments

comment = comments[0]

chain = comment.load_comment_chain(20)
for c in chain:
    print(c)


# TODO filter comments by popularity
# good_comments = get_good_comments(comments)
# print(f"filtered comments is {len(good_comments)} long")