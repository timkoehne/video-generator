import re
from markdown import Markdown
from io import StringIO
import unidecode


def unmark_element(element, stream=None):
    if stream is None:
        stream = StringIO()
    if element.text:
        stream.write(element.text)
    for sub in element:
        unmark_element(sub, stream)
    if element.tail:
        stream.write(element.tail)
    return stream.getvalue()


# patching Markdown
Markdown.output_formats["plain"] = unmark_element  # type: ignore
__md = Markdown(output_format="plain")  # type: ignore
__md.stripTopLevelTags = False  # type: ignore


def remove_markdown(text):
    return __md.convert(text)


def split_text_to_max_x_chars(text: str, x: int) -> list[str]:
    if len(text) > x:
        first_part = text[0:x]

        separate_by = " "
        for sep in [".", ";", ","]:
            if sep in first_part:
                separate_by = sep
                break

        period_index = first_part.rindex(separate_by)
        first_part = text[0 : period_index + 1]
        return [first_part] + split_text_to_max_x_chars(text[period_index + 1 :], x)
    else:
        return [text]


def text_cleanup(text: str) -> str:
    text = remove_markdown(text)

    to_remove_paragraph_if_starts_with = [
        "edit",
        "edit:",
        "tldr",
        "tl;dr",
        "tl:dr",
        "tl,dr",
        "update:",
        "disclaimer",
    ]
    for phrase in to_remove_paragraph_if_starts_with:
        if phrase in text.lower():
            edit_position = text.lower().index(phrase)
            if edit_position < len(text) * 0.3 and "\n" in text[edit_position + 1 :]:
                # print(f"removing {phrase.strip()}")
                text = text.replace(
                    text[edit_position : text.index("\n", edit_position + 1)], ""
                )
            if edit_position > len(text) * 0.6:
                # print(f"removing {phrase.strip()}")
                text = text[0:edit_position]

    to_remove_paragraph_if_included = [
        "throwaway",
        "repost",
        "made this account",
        "is the right subreddit",
        "spelling",
        "formatting", 
        "first time posting",
        "first post",
        "in r/"
    ]
    for phrase in to_remove_paragraph_if_included:
        if phrase in text.lower()[: int(len(text) * 0.3)]:
            edit_position = 0
            if "\n" in text[:edit_position]:
                edit_position = text[:edit_position].rindex("\n")
            text = text.replace(text[edit_position : text.index("\n")], "")

    for match in re.findall("[a-zA-Z]+\n[a-zA-Z]+", text):
        replace_with = ". ".join(match.split("\n"))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    text = " ".join(text.split())
    text = text.replace(" , ", ", ")
    text = text.replace(" . ", ". ")
    text = text.replace("“", '"')

    text = unidecode.unidecode(text)

    for match in re.findall('[a-zA-Z]+"[a-zA-Z]+', text):
        replace_with = " ".join(match.split('"'))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("^--+[\s]", text):
        text = text.replace(match, "")
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("^__+[\s]", text):
        text = text.replace(match, "")
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("[a-zA-Z]\(", text):
        replace_with = " (".join(match.split("("))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("\)[a-zA-Z]", text):
        replace_with = ") ".join(match.split(")"))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("[a-zA-Z],[a-zA-Z]", text):
        replace_with = ", ".join(match.split(","))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("[a-zA-Z] - [a-zA-Z]", text):
        replace_with = ", ".join(match.split(" - "))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("[a-zA-Z] ,[a-zA-Z]", text):
        replace_with = ", ".join(match.split(" ,"))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("\.\.\.\.+", text):
        replace_with = "..."
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    for match in re.findall("[a-zA-Z]\.\.\.[a-zA-Z]", text):
        replace_with = "... ".join(match.split("..."))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    # markdown links
    for match in re.findall("(\[([^\]]+)\]\((\S+(?=\)))\))", text):
        replace_with = match[1]
        # print(f"replacing {match[0]} with {replace_with}")
        text = text.replace(match[0], match[1])

    with open("config/replace_in_text.txt") as file:
        for line in file.readlines():
            line = line.strip("\n")
            replace_from, replace_to = line.split(",")
            # print(f"replacing \"{replace_from}\" with \"{replace_to}\"")
            text = text.replace(replace_from, replace_to)

    # print(self.post_id)
    # print(text)
    return text
