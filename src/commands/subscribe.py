from datetime import timedelta

from command import *
from polling import *
from util import *


def _event_handler(time, args):
    if datetime.today().hour == 0:
        groups = group_query_all({"Subscriptions": {"$exists": True}})
        for group in groups:
            group_id = group["_id"]
            subscriptions = group["Subscriptions"]
            try:
                if "color" in subscriptions:
                    run_group_command(user_get(client.uid), "roll", "color", group_id)
                if "emoji" in subscriptions:
                    run_group_command(user_get(client.uid), "roll", "emoji", group_id)
                if "note" in subscriptions:
                    run_group_command(user_get(client.uid), "note", "", group_id)
            except FBchatException:
                pass
    # - Reset timer
    add_timer(time + timedelta(hours=1), _event_handler, None)


# - Initialize timer
_now = datetime.today()
_next_hour = _now.replace(hour=(_now.hour + 1) % 24, minute=0, second=0, microsecond=0)
add_timer(_next_hour, _event_handler, None)


def _subscribe_handler(author, text, thread_id, thread_type):
    text = text.lower()
    if text not in ("color", "emoji", "note", "restart"):
        return False
    group = group_get(thread_id)
    if "Subscriptions" not in group:
        group["Subscriptions"] = []

    if text in group["Subscriptions"]:
        group["Subscriptions"].remove(text)
        reply = "This conversation has been unsubscribed from {} events.".format(text)
        if not len(group["Subscriptions"]):
            del group["Subscriptions"]
    else:
        group["Subscriptions"].append(text)
        reply = "This conversation has been subscribed to {} events.".format(text)
    client.send(Message(reply), thread_id, thread_type)

    if len(group["Subscriptions"]):
        group_update(thread_id, {"$set": {"Subscriptions": group["Subscriptions"]}})
    else:
        group_update(thread_id, {"$unset": {"Subscriptions": None}})
    return True


_subscribe_info = """<<Subscribe>>
*Usage*: "!subscribe <event>"
*Example*: "!subscribe emoji"
Toggles the group's subscription to <event>. Current events include the following:
-> "Color" - Changes the chat color daily
-> "Emoji" - Changes the chat emoji daily
-> "Note" - Posts the group's !note message daily
-> "Restart" - Notifies the group when Wong restarts"""

map_group_command(["subscribe", "sub", "s"], _subscribe_handler, 0, _subscribe_info)
