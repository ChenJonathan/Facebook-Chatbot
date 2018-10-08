import requests

from command import *
from util import *


def _bully_handler(client, author, args, thread_id, thread_type):
    if not len(args):
        return False
    user = match_user_in_group(client, thread_id, args)
    if user:
        reply = ""
        if user["Priority"] > author["Priority"]:
            reply += "{} is a cool guy.\n\n".format(user["Name"])
            user = author
        url = "https://insult.mattbas.org/api/insult.txt?who=" + user["Name"]
        reply += "{}.".format(requests.get(url).text)
    else:
        reply = "User not found."
    client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
    return True


_bully_info = """<<Bully>>
*Usage*: "!bully <name>"
*Example*: "!bully Justin"
Generates an insult for a user (found using <name>)."""

map_group_command(["bully", "b"], _bully_handler, 0, _bully_info)
