from command import *
from util import *


def _user_to_string(user):
    state, details = user_state(user["_id"])

    text = ["<<{}>>{}".format(user["Name"], (" (" + user["Alias"] + ")") if "Alias" in user else "")]
    text.append("Priority: {}".format(priority_names[user["Priority"]]))
    text.append("Level: {} ({}/100 exp)".format(user["Stats"]["Level"], user["Stats"]["Experience"]))
    text.append("-> ATK: {} ({}{})".format(total_atk(user), base_atk(user), format_num(equip_atk(user), sign=True)))
    text.append("-> DEF: {} ({}{})".format(total_def(user), base_def(user), format_num(equip_def(user), sign=True)))
    text.append("-> SPD: {} ({}{})".format(total_spd(user), base_spd(user), format_num(equip_spd(user), sign=True)))
    text.append("Gold: {} ({} per hour)".format(format_num(user["Gold"], truncate=True),
                                                format_num(user["GoldFlow"], sign=True, truncate=True)))
    text.append("Location: {}".format(user["Location"]))

    return "\n".join(text)


def _check_handler(author, text, thread_id, thread_type):
    if len(text):
        if thread_type == ThreadType.USER:
            user = match_user_by_alias(text)
        else:
            user = match_user_in_group(thread_id, text)
        if not user:
            reply = "User not found."
            client.send(Message(reply), thread_id, thread_type)
            return True
    else:
        user = author

    reply = _user_to_string(user)
    client.send(Message(reply), thread_id, thread_type)
    return True


_check_info = """<<Check>>
*Usage*: "!check <type> <{}>"
*Example*: "!check {}"
*Example*: "!check equip {}"
Lists some information on the user designated by <{}> (or yourself, if left blank)."""

map_user_command(["check", "c"], _check_handler, 0, _check_info.format("alias", "justin", "justin", "alias"))
map_group_command(["check", "c"], _check_handler, 0, _check_info.format("name", "Justin", "Justin", "name"))
