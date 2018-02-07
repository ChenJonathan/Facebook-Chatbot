from fbchat.models import *
from datetime import datetime
import random
import threading

from emoji import random_emoji
from mongo import *

def apply_gold_rates():
    for user in user_get_all():
        gold_add(user['_id'], user['gold_rate'])

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

def reset_timer(client):
    client.explore_record.clear()
    apply_gold_rates()
    if datetime.today().hour == 0:
        manage_subscriptions(client)

    set_timer(client)

def set_timer(client):
    now = datetime.today()
    later = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    delta_time = (later - now).seconds + 1
    threading.Timer(delta_time, reset_timer, [client]).start()