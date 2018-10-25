from command import *
from util import *


def _perm_handler(author, text, thread_id, thread_type):
    try:
        priority, text = split(text)
        priority = int(priority)
        assert len(text)
    except:
        return False
    if thread_type == ThreadType.USER:
        user = match_user_by_alias(text)
    else:
        user = match_user_in_group(thread_id, text)
    if not user:
        reply = "User not found."
    elif user['_id'] == master_id:
        reply = "Cannot modify {} priority.".format(priority_names[master_priority])
    elif priority < 0 or priority >= master_priority:
        reply = "Invalid priority value."
    else:
        user_update(user["_id"], {"$set": {"Priority": priority}})
        reply = "{}'s priority has been set to {} ({}).".format(user['Name'], priority, priority_names[priority])
    client.send(Message(reply), thread_id, thread_type)
    return True


_perm_info = """<<Perm>>
*Usage*: "!perm <priority> <{}>"
*Example*: "!perm 0 {}"
Sets the priority of the user designated by <{}> to <priority>."""

map_user_command(["perm", "p"], _perm_handler, 4, _perm_info.format("alias", "raph", "alias"))
map_group_command(["perm", "p"], _perm_handler, 4, _perm_info.format("name", "Raphael", "name"))
