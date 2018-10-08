from command import *
from util import *


def _message_handler(client, author, args, thread_id, thread_type):
    alias, reply = split(args)
    if not len(alias):
        return False
    user = match_user_by_alias(alias)
    if not user:
        client.send(Message("User not found."), thread_id=thread_id)
    elif len(reply):
        client.send(Message(reply), thread_id=user["_id"])
    else:
        client.send(Message(emoji_size=EmojiSize.SMALL), thread_id=user["_id"])
    return True


_message_info = """<<Message>>
Usage: "!message <alias> <message>"
Example: "!message raph Hi! This is Wong."
Sends a message from Wong to the user designated by <alias>. Only usable by {} priority.

Usage: "!message <alias>"
Example: "!message raph"
Sends the default chat emoji from Wong to the user designated by <alias>. Only usable by {} priority.""".format(
    priority_names[4], priority_names[4])

map_user_command(["message", "m"], _message_handler, 4, _message_info)
