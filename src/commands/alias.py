from command import *
from util import *


def _alias_handler(author, text, thread_id, thread_type):
    alias, user = split(text)
    alias = alias.lower()
    if not len(alias):
        return False

    elif len(user):
        if thread_type == ThreadType.USER:
            user = match_user_by_search(user)
        else:
            user = match_user_in_group(thread_id, user)
        existing = user_query_one({"Alias": alias})
        if existing:
            user_update(existing["_id"], {"$unset": {"Alias": None}})
        user_update(user["_id"], {"$set": {"Alias": alias}})
        reply = "{}'s alias has been set to {}.".format(user["Name"], alias)

    elif alias == "list":
        users = user_query_all({"Alias": {"$exists": True}})
        users = sorted(users, key=lambda x: x["Alias"])
        reply = "<<Aliases>>\n" + "\n".join(["*{}*: {}".format(i["Alias"], i["Name"]) for i in users])

    else:
        existing = user_query_one({"Alias": alias})
        if existing:
            user_update(existing["_id"], {"$unset": {"Alias": None}})
            reply = "{}'s alias has been unset.".format(existing["Name"])
        else:
            reply = "Alias not found."

    client.send(Message(reply), thread_id, thread_type)
    return True


_alias_info = """<<Alias>>
*Usage*: "!alias <alias> <name>"
*Example*: "!alias wong Wong Liu"
Assigns an alias to a user (found using <name>) for use in other private chat commands. Aliases must be a single word.

*Usage*: "!alias <alias>"
Removes an existing alias.

*Usage*: "!alias list"
Lists all active aliases."""

map_user_command(["alias"], _alias_handler, 3, _alias_info)
map_group_command(["alias"], _alias_handler, 3, _alias_info)
