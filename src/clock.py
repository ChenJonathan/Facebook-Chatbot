from fbchat.models import *
from datetime import datetime
import random
import threading
import traceback

from data import random_emoji
from mongo import *
from util import *


def apply_gold_rates():
    for user in user_get_all():
        gold_add(user['_id'], user['GoldFlow'])


def restore_health(client):
    for user_id, health in list(client.user_health.items()):
        state, details = client.user_states.get(user_id, (UserState.Idle, {}))
        if state != UserState.Battle:
            del client.user_health[user_id]


def manage_subscriptions(client):
    colors = list(ThreadColor)
    for group_id, subscriptions in subscription_get_all().items():
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
        client.explore_record.clear()
        apply_gold_rates()
        restore_health(client)
        if datetime.today().hour == 0:
            manage_subscriptions(client)
    except:
        client.send(Message('Timer: ' + traceback.format_exc()), thread_id=master_id)
    finally:
        lock.release()

    set_timer(client, lock)


def set_timer(client, lock):
    now = datetime.today()
    later = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    delta_time = (later - now).seconds + 1
    threading.Timer(delta_time, reset_timer, [client, lock]).start()