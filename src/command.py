from fbchat.models import *

from util import *

_user_map = {}
_group_map = {}
_define_map = load_state("Defines")


def run_user_command(author, command, text, thread_id):
    if command not in _user_map:
        client.send(Message("Not a valid command."), thread_id=thread_id)
        return False
    mapping = _user_map[command]

    if author["Priority"] < mapping[1]:
        client.send(Message("You don't have permission to do this."), thread_id=thread_id)
    elif not mapping[0](author, text, thread_id, ThreadType.USER):
        run_user_command(author, "help", command, thread_id)
    else:
        return True
    return False


def map_user_command(mappings, handler, priority, info):
    for mapping in mappings:
        _user_map[mapping] = (handler, priority, info)


def run_group_command(author, command, text, thread_id):
    if command in _define_map:
        mapping = _define_map[command]
        if mapping[0] == '!':
            command, text = split(mapping)
            command = command[1:].lower()
            text = text.strip()
            return run_group_command(author, command, text, thread_id)
        else:
            client.send(Message(mapping), thread_id=thread_id, thread_type=ThreadType.GROUP)
            return True

    if command not in _group_map:
        client.send(Message("Not a valid command."), thread_id=thread_id, thread_type=ThreadType.GROUP)
        return False
    mapping = _group_map[command]

    if author["Priority"] < mapping[1]:
        client.send(Message("You don't have permission to do this."), thread_id=thread_id, thread_type=ThreadType.GROUP)
    elif not mapping[0](author, text, thread_id, ThreadType.GROUP):
        run_group_command(author, "help", command, thread_id)
    else:
        return True
    return False


def map_group_command(mappings, handler, priority, info):
    for mapping in mappings:
        _group_map[mapping] = (handler, priority, info)


# Define command

def _define_handler(author, text, thread_id, thread_type):
    command, text = split(text)
    if not len(command):
        return False
    elif command in _group_map and author["Priority"] < 3:
        reply = "You don't have permission to do this."
    elif len(text):
        _define_map[command] = text
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
*Usage*: "!define <command> <mapping>"
*Example*: "!define quit !mute"
Maps <command> so that using it has the effect of the command specified in <mapping>. If <mapping> is not a command, \
Wong will instead send <mapping> as a message.

*Usage*: "!define <command>"
Clears the mapping for <command>."""

map_user_command(["define", "d"], _define_handler, 2, _define_info)
map_group_command(["define", "d"], _define_handler, 2, _define_info)


# Help command

_user_strings = [
    (0, "!alarm: Set an alarm"),
    (3, "!alias: Alias assignment"),
    (0, "!check: See user statistics"),
    (2, "!define: Command mapping"),
    (0, "!help: Read documentation"),
    (4, "!message: Gateway messaging"),
    (0, "!note: Save and view notes"),
    (4, "!perm: Change user priority"),
    (2, "!quest: Solve quizzes for gold"),
    (2, "!response: Response priming"),
    (2, "!roll: Roll the dice"),
    (2, "!secret: List active secrets"),
    (3, "!wong: Talk to Wong")
]

_group_strings = [
    (0, "<Game Commands>"),
    (0, "!check: See user statistics"),
    (0, "!duel: Duel another player"),
    (0, "!quest: Solve quizzes for gold"),
    (0, "!score: Show group rankings"),
    (0, ""),
    (0, "<Miscellaneous Commands>"),
    (0, "!alarm: Set an alarm"),
    (0, "!bully: Harass someone"),
    (0, "!help: Read documentation"),
    (0, "!mute: Remove from group"),
    (0, "!note: Save and view notes"),
    (0, "!roll: Roll the dice"),
    (0, "!subscribe: Subscribe to events"),
    (0, "!wong: Talk to Wong")
]


def _help_handler(author, text, thread_id, thread_type):
    if len(text):
        text = text.lower()
        current_map = _user_map if thread_type == ThreadType.USER else _group_map
        if text in current_map:
            if author["Priority"] >= current_map[text][1]:
                reply = current_map[text][2]
            else:
                reply = "You don't have permission to do this."
        elif thread_type == ThreadType.GROUP and text in _define_map:
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
*Usage*: "!help"
Lists all the group commands that you can use.

*Usage*: "!help <command>"
*Example*: "!help quest"
Explains the syntax and effects of the provided group <command>."""

map_user_command(["help", "h"], _help_handler, 0, _help_info)
map_group_command(["help", "h"], _help_handler, 0, _help_info)

from commands import *
