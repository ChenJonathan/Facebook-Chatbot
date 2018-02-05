from fbchat.models import *
from datetime import datetime
import random
import threading

from mongo import *

def apply_gold_rates():
    for user in user_get_all():
        gold_add(user['_id'], user['gold_rate'])

def manage_subscriptions():
    colors = list(ThreadColor)
    for group_id, subscriptions in subscription_get_all().items():
        group = self.fetchGroupInfo(group_id)[group_id]
        if 'color' in subscriptions:
            color = group.color
            while color == group.color:
                color = random.choice(colors)
            self.changeThreadColor(color, thread_id=group_id)
        if 'emoji' in subscriptions:
            emoji = group.emoji
            while emoji == group.emoji:
                emoji = random_emoji()
            self.changeThreadEmoji(emoji, thread_id=group_id)

def reset_timer():
    set_timer()

    apply_gold_rates()
    if now.hour == 0:
        manage_subscriptions()

def set_timer():
    now = datetime.today()
    later = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    delta_time = (later - now).seconds + 1
    threading.Timer(delta_time, reset_timer).start()