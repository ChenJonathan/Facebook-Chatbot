from command import *
from util import *


def _mute_handler(author, text, thread_id, thread_type):
    if not len(text):
        return False
    elif not bot_is_admin(thread_id):
        reply = "I don't have permission to do this."
        client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
        return True

    user = match_user_in_group(thread_id, text)
    if user:
        if user["Priority"] > author["Priority"]:
            client.removeUserFromGroup(author["_id"], thread_id)
        else:
            client.removeUserFromGroup(user["_id"], thread_id)
    else:
        reply = "User not found."
        client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
    return True


_mute_info = """<<Mute>>
*Usage*: "!mute <name>"
*Example*: "!mute Justin"
Kicks a user (found using <name>) from the group chat."""

map_group_command(["mute", "m"], _mute_handler, 0, _mute_info)
