import dateparser

from command import *
from consume import *
from polling import *
from util import *

_alarms = load_state("Alarms")
_prompts = {}


def _alarm_thread(time):
    modified = False
    for thread_id, alarm_list in list(_alarms.items()):
        while len(alarm_list) and time.timestamp() > alarm_list[0]["Time"]:
            alarm = alarm_list.pop(0)
            reply = "An alarm has gone off!\n\n{}".format(alarm["Note"])
            thread_type = client.fetchThreadInfo(thread_id)[thread_id].type
            client.send(Message(reply), thread_id, thread_type)
            modified = True
        if not len(alarm_list):
            del _alarms[thread_id]
    if modified:
        save_state("Alarms", _alarms)


add_thread(_alarm_thread)


def _prompt_handler(author, text, thread_id, thread_type):
    timestamp = _prompts.pop((author["_id"], thread_id), None)
    if timestamp is None:
        return True
    if thread_id not in _alarms:
        _alarms[thread_id] = []
    index = 0
    while index < len(_alarms[thread_id]) and _alarms[thread_id][index]["Time"] < timestamp:
        index += 1
    _alarms[thread_id].insert(index, {"Time": timestamp, "Note": text})
    client.send(Message("The alarm has been set!"), thread_id=thread_id, thread_type=thread_type)
    save_state("Alarms", _alarms)
    return True


def _alarm_handler(author, text, thread_id, thread_type):
    if text.lower() == "cancel":
        reply = "All alarms have been cancelled for this chat."
        if (author["_id"], thread_id) in _prompts:
            del _prompts[(author["_id"], thread_id)]
            reply = "The alarm has been cancelled."
        elif thread_id in _alarms:
            del _alarms[thread_id]
            save_state("Alarms", _alarms)

    elif len(text):
        date = dateparser.parse(text, languages=["en"])
        if date:
            if (author["_id"], thread_id) not in _prompts:
                add_consumption(_prompt_handler, author["_id"], thread_id, thread_type)
            _prompts[(author["_id"], thread_id)] = date.timestamp()
            reply = "Alarm set at {}. ".format(date.strftime("%b %d %Y, %I:%M %p"))
            reply += "Please enter a note for this alarm or use \"!alarm cancel\" to cancel:"
        else:
            reply = "Not a valid time format."

    elif thread_id in _alarms:
        reply = "<<Alarms>>\n"
        for alarm in _alarms[thread_id]:
            time_string = datetime.fromtimestamp(alarm["Time"]).strftime("%b %d %Y, %I:%M %p")
            reply += "*{}*\n-> {}\n".format(time_string, alarm["Note"])

    else:
        reply = "There are no alarms set for this chat."
    client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)
    return True


_alarm_info = """<<Alarm>>
*Usage*: "!alarm"
Displays all alarms for this chat.

*Usage*: "!alarm <time>"
*Example*: "!alarm tomorrow at 7 pm"
Sets an alarm for the specified <time>. Formatting is lenient.

*Usage*: "!alarm cancel"
Cancels all alarms for this chat."""

map_user_command(["alarm", "a"], _alarm_handler, 0, _alarm_info)
map_group_command(["alarm", "a"], _alarm_handler, 0, _alarm_info)
