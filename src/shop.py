from fbchat.models import *
import random

from data import random_beast
from mongo import *


def generate_shop_info(client, user, thread_id):
    reply = 'Shop information has been sent to you. Check your private messages (or message requests).'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = ['<<The Wong Shoppe>>']
    reply.append('Buy things with "!shop <item>" in a group chat.\n')
    reply.append('1. Charity donation: 100 gold')
    reply.append('-> Donates some gold to your local charity.\n')
    reply.append('2. Life Elixir: 1000 gold')
    reply.append('-> Restores your life to its maximum.\n')
    reply.append('3. Hunting pet: 2500 gold')
    reply.append('-> Hunts monsters for you, granting some gold every hour.\n')
    reply.append('4. Hunting pet x 10: 25000 gold')
    reply.append('-> Hunts monsters for you, granting some gold every hour.\n')
    reply.append('5. Hunting pet x 100: 250000 gold')
    reply.append('-> Hunts monsters for you, granting some gold every hour.')
    reply = '\n'.join(reply)
    client.send(Message(reply), thread_id=user['_id'])


def shop_purchase(client, user, slot, thread_id):
    try:
        slot = int(slot)
        assert 0 < slot <= 5
    except:
        reply = 'Invalid slot number.'
    else:
        gold = user['Gold']
        if slot == 1:
            if gold >= 100:
                gold_add(user['_id'], -100)
                _charity_donation(client, thread_id)
                return
            else:
                reply = 'You can\'t afford that.'
        elif slot == 2:
            if user['_id'] not in client.user_health or client.user_health[user['_id']] == user['Stats']['HP']:
                reply = 'You already have full health.'
            elif gold >= 1000:
                gold_add(user['_id'], -1000)
                _life_elixir(client, user, thread_id)
                return
            else:
                reply = 'You can\'t afford that.'
        elif slot == 3:
            if gold >= 2500:
                gold_add(user['_id'], -2500)
                _hunting_pet(client, user, 1, thread_id)
                return
            else:
                reply = 'You can\'t afford that.'
        elif slot == 4:
            if gold >= 25000:
                gold_add(user['_id'], -25000)
                _hunting_pet(client, user, 10, thread_id)
                return
            else:
                reply = 'You can\'t afford that.'
        elif slot == 5:
            if gold >= 250000:
                gold_add(user['_id'], -250000)
                _hunting_pet(client, user, 100, thread_id)
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
    user_id = user['_id']
    client.user_health[user_id] = user['Stats']['HP']
    reply = 'Your health has been restored to its maximum!'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def _hunting_pet(client, user, multiplier, thread_id):
    beast = random_beast()
    delta_rate = beast[1] * beast[2] * multiplier
    gold_rate_add(user['_id'], delta_rate)
    if multiplier == 1:
        reply = 'You\'ve bought a ' + str(beast[1]) + '/' + str(beast[2])
        reply += ' ' + beast[0] + '! It grants you an additional ' + str(delta_rate) + ' gold per hour.'
    else:
        reply = 'You\'ve bought ' + str(multiplier) + ' ' + str(beast[1]) + '/' + str(beast[2])
        reply += ' ' + beast[0] + 's! They grant you an additional ' + str(delta_rate) + ' gold per hour.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)