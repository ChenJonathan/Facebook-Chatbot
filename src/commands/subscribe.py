from datetime import timedelta
import random

from command import *
from data import random_emoji
from polling import *
from util import *


def _event_handler(client, time, args):
    if datetime.today().hour == 0:
        colors = list(ThreadColor)
        groups = group_query_all({"Subscriptions": {"$exists": True}})
        for group in groups:
            group_id = group["_id"]
            subscriptions = group["Subscriptions"]
            try:
                group = client.fetchGroupInfo(group_id)[group_id]
            except FBchatException:
                pass

            if "color" in subscriptions:
                color = group.color
                while color == group.color:
                    color = random.choice(colors)
                client.changeThreadColor(color, thread_id=group_id)
            if "emoji" in subscriptions:
                emoji = group.emoji
                while emoji == group.emoji:
                    emoji = random_emoji()
                client.changeThreadEmoji(emoji, thread_id=group_id)
            if "note" in subscriptions:
                run_group_command(client, user_get(client.uid), "note", "", group_id)

    # - Reset timer
    add_timer(time + timedelta(hours=1), _event_handler, None)


# Initialize timer
_now = datetime.today()
_next_hour = _now.replace(hour=(_now.hour + 1) % 24, minute=0, second=0, microsecond=0)
add_timer(_next_hour, _event_handler, None)


def _subscribe_handler(client, author, args, thread_id, thread_type):
    args = args.lower()
    if args not in ("color", "emoji", "note"):
        return False
    group = group_get(thread_id)
    if "Subscriptions" not in group:
        group["Subscriptions"] = []

    if args in group["Subscriptions"]:
        group["Subscriptions"].remove(args)
        reply = "This conversation has been unsubscribed from {} events.".format(args)
        if not len(group["Subscriptions"]):
            del group["Subscriptions"]
    else:
        group["Subscriptions"].append(args)
        reply = "This conversation has been subscribed to daily {} events.".format(args)
    client.send(Message(reply), thread_id=thread_id, thread_type=thread_type)

    if "Subscriptions" in group:
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
-> "Note" - Posts the group's !note message daily"""

map_group_command(["subscribe", "sub", "s"], _subscribe_handler, 0, _subscribe_info)
