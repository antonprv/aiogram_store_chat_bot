from emoji import replace_emoji


def strip_emojis(text):
    return replace_emoji(text, replace='')
