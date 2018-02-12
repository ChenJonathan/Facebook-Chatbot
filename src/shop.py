from fbchat.models import *
import random

from data import random_beast
from mongo import *


def generate_shop_info(client, user, thread_id):
    reply = 'Shop information has been sent to you. Check your private messages (or message requests).'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = ['<<The Wong Shoppe>>']
    reply.append('Buy things with "!shop <item>" in a group chat.\n')
    reply.append('1. 0100 gold: Charity donation')
    reply.append('-> Donates some gold to your local charity.\n')
    reply.append('2. 1000 gold: Life Elixir')
    reply.append('-> Restores your life to its maximum.\n')
    reply.append('3. 2500 gold: Hunting pet')
    reply.append('-> Hunts monsters for you, granting some gold every hour.')
    reply = '\n'.join(reply)
    client.send(Message(reply), thread_id=user['_id'])


def shop_purchase(client, user, slot, thread_id):
    try:
        slot = int(slot) - 1
    except:
        reply = 'Invalid slot number.'
    else:
        gold = user['Gold']
        if slot == 0:
            if gold >= 100:
                gold_add(user['_id'], -100)
                _charity_donation(client, thread_id)
                return
            else:
                reply = 'You can\'t afford that.'
        elif slot == 1:
            if user['_id'] not in client.user_health or client.user_health[user['_id']] == user['Stats']['HP']:
                reply = 'You already have full health.'
            elif gold >= 1000:
                gold_add(user['_id'], -1000)
                _life_elixir(client, user, thread_id)
                return
            else:
                reply = 'You can\'t afford that.'
        elif slot == 2:
            if gold >= 2500:
                gold_add(user['_id'], -2500)
                _hunting_pet(client, user, thread_id)
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


def _life_elixir(client, user, thread_id):
    client.user_health[user['_id']] = user['Stats']['HP']
    reply = 'Your health has been restored to its maximum!'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def _hunting_pet(client, user, thread_id):
    beast = random_beast()
    delta_rate = beast[1] * beast[2]
    gold_rate_add(user['_id'], delta_rate)
    reply = 'You\'ve bought a ' + str(beast[1]) + '/' + str(beast[2])
    reply += ' ' + beast[0] + '! It grants you an additional '
    reply += str(delta_rate) + ' gold per hour.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)