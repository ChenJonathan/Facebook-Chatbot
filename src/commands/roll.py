import random

from command import *
from data import random_emoji
from util import *


def _roll_handler(author, text, thread_id, thread_type):
    arg, text = partition(text, ["color", "emoji"])
    if arg is None:
        if not len(text):
            text = 6
        try:
            text = int(text)
            assert text > 0
        except:
            return False
        roll = str(random.randint(1, text))
        an = roll[0] == "8" or ((roll[:2] == "11" or roll[:2] == "18") and len(roll) % 3 == 2)
        reply = "{} rolls {} {}.".format(author["Name"], "an" if an else "a", roll)
        client.send(Message(reply), thread_id, thread_type)

    else:
        if thread_type == ThreadType.USER:
            thread = client.fetchUserInfo(thread_id)[thread_id]
        else:
            thread = client.fetchGroupInfo(thread_id)[thread_id]
        if arg == "color":
            color, colors = thread.color, list(ThreadColor)
            while color == thread.color:
                color = random.choice(colors)
            client.changeThreadColor(color, thread_id)
        elif arg == "emoji":
            emoji = thread.emoji
            while emoji == thread.emoji:
                emoji = random_emoji()
            client.changeThreadEmoji(emoji, thread_id)
    return True


_roll_info = """<<Roll>>
*Usage*: "!roll <sides>"
*Example*: "!roll 10"
Rolls a <sides> sided die. <sides> defaults to 6 if left blank.

*Usage*: "!roll color"
Randomly changes the chat color.

*Usage*: "!roll emoji"
Randomly changes the chat emoji."""

map_user_command(["roll"], _roll_handler, 0, _roll_info)
map_group_command(["roll", "r"], _roll_handler, 0, _roll_info)
