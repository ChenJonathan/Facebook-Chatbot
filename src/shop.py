from fbchat.models import *
import random

from hearthstone import random_beast
from mongo import *

def generate_shop_info(client, user, thread_id):
    reply = 'Shop information been sent to you in private chat.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = ['<<The Wong Shoppe>>']
    reply.append('1. 0100 gold: Charity donation')
    reply.append('2. 1000 gold: Random hunting pet')
    reply.append('(Buy things with "!shop <item>" in a group chat)')
    reply = '\n'.join(reply)
    client.send(Message(reply), thread_id=user['_id'], thread_type=ThreadType.USER)

def shop_purchase(client, user, slot, thread_id):
    try:
        slot = int(slot)
    except:
        reply = 'Invalid slot number.'
    else:
        gold = gold_get(author_id)
        if slot == 1:
            if gold >= 100:
                gold_add(user['_id'], 100)
                _charity_donation(client, thread_id)
                return
            else:
                reply = 'You can\'t afford that.'
        elif slot == 2:
            if gold >= 1000:
                gold_add(user['_id'], 1000)
                _random_hunting_pet(client, user, thread_id)
                return
            else:
                reply = 'You can\'t afford that.'
        else:
            reply = 'Invalid slot number.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def _charity_donation(client, thread_id):
    charities = [
        'Flat Earth Society', 
        'Westboro Baptist Church', 
        'Church of Scientology'
    ]
    reply = 'The ' + random.choice(charities) + ' thanks you for your donation.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def _random_hunting_pet(client, user, thread_id):
    beast = random_beast()
    delta_rate = beast[1] * beast[2]
    gold_rate_add(user['_id'], delta_rate)
    reply = 'You\'ve bought a ' + str(beast[1]) + '/' + str(beast[2])
    reply += ' ' + beast[0] + '! It grants you an additional '
    reply += str(delta_rate) + ' gold per hour.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)