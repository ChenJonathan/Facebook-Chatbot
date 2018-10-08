from fbchat.models import *
from datetime import datetime
import random
import threading
import traceback

from data import random_emoji
from util import *


def manage_subscriptions(client):
    colors = list(ThreadColor)
    groups = group_query_all({'Subscriptions': {'$exists': True}})
    for group in groups:
        group_id = group["_id"]
        subscriptions = group["Subscriptions"]
        group = client.fetchGroupInfo(group_id)[group_id]
        if 'color' in subscriptions:
            color = group.color
            while color == group.color:
                color = random.choice(colors)
            client.changeThreadColor(color, thread_id=group_id)
        if 'emoji' in subscriptions:
            emoji = group.emoji
            while emoji == group.emoji:
                emoji = random_emoji()
            client.changeThreadEmoji(emoji, thread_id=group_id)


def reset_timer(client, lock):
    lock.acquire()
    try:
        if datetime.today().hour == 0:
            manage_subscriptions(client)
    except:
        stack = 'Timer: ' + traceback.format_exc()
        print(stack)
        client.send(Message(stack), thread_id=master_id)
    finally:
        lock.release()

    set_timer(client, lock)


def set_timer(client, lock):
    now = datetime.today()
    later = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    delta_time = (later - now).seconds + 1
    threading.Timer(delta_time, reset_timer, [client, lock]).start()