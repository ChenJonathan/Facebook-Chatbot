from command import *
from util import *


def _message_handler(author, text, thread_id, thread_type):
    alias, reply = split(text)
    if not len(alias):
        return False
    user = match_user_by_alias(alias)
    if not user:
        client.send(Message("User not found."), thread_id, thread_type)
    elif len(reply):
        client.send(Message(reply), user["_id"], ThreadType.USER)
    else:
        client.send(Message(emoji_size=EmojiSize.SMALL), user["_id"], ThreadType.USER)
    return True


_message_info = """<<Message>>
*Usage*: "!message <alias> <message>"
*Example*: "!message raph Hi! This is Wong."
Sends a message from Wong to the user designated by <alias>.

*Usage*: "!message <alias>"
*Example*: "!message raph"
Sends the default chat emoji from Wong to the user designated by <alias>."""

map_user_command(["message", "m"], _message_handler, 4, _message_info)
