from fbchat.models import *

from util import *

_user_map = {}
_group_map = {}
_define_map = load_state("Defines")


def run_user_command(client, author, command, args):
    if command not in _user_map:
        client.send(Message("Not a valid command."), thread_id=author["_id"])
        return False
    mapping = _user_map[command]

    if author["Priority"] < mapping[1]:
        client.send(Message("You don't have permission to do this."), thread_id=author["_id"])
    elif not mapping[0](client, author, args, author["_id"], ThreadType.USER):
        run_user_command(client, author, "help", command)
    else:
        return True
    return False


def map_user_command(mappings, handler, priority, info):
    for mapping in mappings:
        _user_map[mapping] = (handler, priority, info)


def run_group_command(client, author, command, args, thread_id):
    if command in _define_map:
        mapping = _define_map[command]
        if mapping[0] == '!':
            command, args = split(mapping)
            command = command[1:].lower()
            args = args.strip()
            return run_group_command(client, author, command, args, thread_id)
        else:
            client.send(Message(mapping), thread_id=thread_id, thread_type=ThreadType.GROUP)
            return True

    if command not in _group_map:
        client.send(Message("Not a valid command."), thread_id=thread_id, thread_type=ThreadType.GROUP)
        return False
    mapping = _group_map[command]

    if author["Priority"] < mapping[1]:
        client.send(Message("You don't have permission to do this."), thread_id=thread_id, thread_type=ThreadType.GROUP)
    elif not mapping[0](client, author, args, thread_id, ThreadType.GROUP):
        run_group_command(client, author, "help", command, thread_id)
    else:
        return True
    return False


def map_group_command(mappings, handler, priority, info):
    for mapping in mappings:
        _group_map[mapping] = (handler, priority, info)


# Define command

def _define_handler(client, author, args, thread_id, thread_type):
    command, args = split(args)
    if not len(command):
        return False
    elif command in _group_map and author["Priority"] < 3:
        reply = "You don't have permission to do this."
    elif len(args):
        _define_map[command] = args
        reply = "!{} has been defined!".format(command)
    elif command in _define_map:
        del _define_map[command]
        reply = "!{} has been cleared.".format(command)
    else:
        reply = "!{} does not exist.".format(command)
    client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
    save_state("Defines", _define_map)
    return True


_define_info = """<<Define>>
Usage: "!define <command> <mapping>"
Example: "!define quit !mute"
Maps <command> so that using it has the effect of the command specified in <mapping>. If <mapping> is not a command, \
Wong will instead send <mapping> as a message. Only usable by {} priority and above.

Usage: "!define <command>"
Clears the mapping for <command>. Only usable by {} priority and above.""".format(priority_names[2], priority_names[2])

map_user_command(["define", "d"], _define_handler, 2, _define_info)
map_group_command(["define"], _define_handler, 2, _define_info)


# Help command

_user_strings = [
    (3, "!alias: Alias assignment"),
    (0, "!check: See user statistics"),
    (2, "!define: Command mapping"),
    (3, "!equip: Change level / stats"),
    (0, "!help: Read documentation"),
    (4, "!message: Gateway messaging"),
    (4, "!perm: Change user priority"),
    (2, "!response: Response priming"),
    (2, "!secret: List active secrets"),
    (3, "!warp: Change location")
]

_group_strings = [
    (0, "<Game Commands>"),
    (0, "!battle: Battle monsters"),
    (0, "!check: See user statistics"),
    (0, "!craft: Craft items with materials"),
    (0, "!duel: Duel another player"),
    (0, "!explore: Gather materials"),
    (0, "!give: Give someone gold"),
    (0, "!inventory: Check your inventory"),
    (0, "!jail: Send someone to jail"),
    (0, "!map: See your location"),
    (0, "!quest: Solve quizzes for gold"),
    (0, "!score: Show group rankings"),
    (0, "!shop: Spend gold to buy things"),
    (0, "!talent: Allocate talent points"),
    (0, "!travel: Travel around the world"),
    (0, ""),
    (0, "<Miscellaneous Commands>"),
    (0, "!bully: Harass someone"),
    (0, "!daily: Subscribe to daily events"),
    (0, "!help: Read documentation"),
    (0, "!mute: Remove from group"),
    (0, "!notes: See recent changes"),
    (0, "!random: Random emoji / color"),
    (0, "!roll: Roll the dice")
]


def _help_handler(client, author, args, thread_id, thread_type):
    if len(args):
        args = args.lower()
        current_map = _user_map if thread_type == ThreadType.USER else _group_map
        if args in current_map:
            reply = current_map[args][2]
        elif thread_type == ThreadType.GROUP and args in _define_map:
            reply = "This is a redefined command."
        else:
            reply = "Not a valid command."
    else:
        priority = author["Priority"]
        reply = "<<Command List>>\n(See how commands work with \"!help <command>\")\n"
        strings = _user_strings if thread_type == ThreadType.USER else _group_strings
        for required_priority, string in strings:
            if priority >= required_priority:
                reply += "\n" + string
    client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
    return True


_help_info = """<<Help>>
Usage: "!help"
Lists all the group commands that you can use.

Usage: "!help <command>"
Example: "!help quest"
Explains the syntax and effects of the provided group <command>."""

map_user_command(["help", "h"], _help_handler, 0, _help_info)
map_group_command(["help", "h"], _help_handler, 0, _help_info)

from commands import *
