from command import *
from util import *


def _alias_handler(client, author, args, thread_id, thread_type):
    alias, user = split(args)
    alias = alias.lower()
    if not len(alias):
        return False

    elif len(user):
        if thread_type == ThreadType.USER:
            user = match_user_by_search(client, user)
        else:
            user = match_user_in_group(client, thread_id, user)
        existing = user_query_one({"Alias": alias})
        if existing:
            user_update(existing["_id"], {"$unset": {"Alias": None}})
        user_update(user["_id"], {"$set": {"Alias": alias}})
        reply = "{}'s alias has been set to {}.".format(user["Name"], alias)

    else:
        existing = user_query_one({"Alias": alias})
        if existing:
            user_update(existing["_id"], {"$unset": {"Alias": None}})
            reply = "{}'s alias has been unset.".format(existing["Name"])
        else:
            reply = "Alias not found."

    client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
    return True


_alias_info = """<<Alias>>
Usage: "!alias <alias> <name>"
Example: "!alias wong Wong Liu"
Assigns an alias to a user (found using <name>) for use in other private chat commands. Aliases must be a single word. \
Only usable by {} priority and above.

Usage: "!alias <alias>"
Removes an existing alias. Only usable by {} priority and above.""".format(priority_names[3], priority_names[3])

map_user_command(["alias", "a"], _alias_handler, 3, _alias_info)
map_group_command(["alias", "a"], _alias_handler, 3, _alias_info)
