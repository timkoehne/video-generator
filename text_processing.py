import re
import emoji


def split_text_to_max_x_chars(text: str, x: int) -> list[str]:
    if len(text) > x:
        first_part = text[0:x]
        period_index = first_part.rindex(".")
        first_part = text[0 : period_index + 1]
        return [first_part] + split_text_to_max_x_chars(text[period_index + 1 :], x)
    else:
        return [text]


def text_cleanup(text: str) -> str:
    to_remove = ["\nedit", "*edit", "\ntldr", "\ntl;dr", "update:"]
    for phrase in to_remove:
        if phrase in text.lower():
            edit_position = text.lower().index(phrase)
            if edit_position > len(text) * 0.4:
                # print(f"removing {phrase.strip()}")
                text = text[0:edit_position]

    text = " ".join(text.split())
    text = text.replace(" , ", ", ")
    text = text.replace(" . ", ". ")
    text = text.replace("“", '"')
    text = emoji.replace_emoji(text, "")

    for match in re.findall('[a-zA-Z]+"[a-zA-Z]+', text):
        replace_with = " ".join(match.split('"'))
        text = text.replace(match, replace_with)
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
        
    for match in re.findall("[a-zA-Z]\.\.\.[a-zA-Z]", text):
        replace_with = "... ".join(match.split("..."))
        text = text.replace(match, replace_with)
        # print(f"replacing {match} with {replace_with}")

    # markdown links
    for match in re.findall("(\[([^\]]+)\]\((\S+(?=\)))\))", text):
        replace_with = match[1]
        # print(f"replacing {match[0]} with {replace_with}")
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
    # print(text)
    return text
