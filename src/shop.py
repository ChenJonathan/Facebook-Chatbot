from fbchat.models import *
import random

from data import random_beast
from mongo import *
from util import *


def generate_shop_info(client, user, thread_id):
    gold = user['Gold']
    healthy = client.user_health.get(user['_id'], user['Stats']['Health']) == user['Stats']['Health']
    reply = 'Shop information has been sent to you. Check your private messages (or message requests).'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = ['<<The Wong Shoppe>>']
    reply.append('Buy things with "!shop <slot> <amount>" in a group chat. <amount> defaults to 1 if left blank.\n')
    reply.append('1. Charity donation: 100 gold (' + str(max(gold // 100, 0)) + ' max)')
    reply.append('-> Donates some gold to your local charity.\n')
    reply.append('2. Life Elixir: 1000 gold (' + ('1' if gold >= 1000 and not healthy else '0') + ' max)')
    reply.append('-> Restores your life to its maximum.\n')
    reply.append('3. Hunting pet: 2500 gold (' + str(max(gold // 2500, 0)) + ' max)')
    reply.append('-> Hunts monsters for you, granting some gold every hour.')
    reply = '\n'.join(reply)
    client.send(Message(reply), thread_id=user['_id'])


def shop_purchase(client, user, slot, amount, thread_id):
    if slot <= 0 or slot > 3:
        reply = 'Invalid slot number.'
    elif amount < 1:
        reply = 'Invalid purchase amount.'
    else:
        gold = user['Gold']
        if slot == 1:
            if gold < amount * 100:
                reply = 'You can\'t afford that.'
            else:
                gold_add(user['_id'], amount * -100)
                _charity_donation(client, thread_id)
                return
        elif slot == 2:
            if amount > 1:
                reply = 'You can\'t buy multiple life elixirs at once.'
            elif gold < 1000:
                reply = 'You can\'t afford that.'
            elif client.user_health.get(user['_id'], user['Stats']['Health']) == user['Stats']['Health']:
                reply = 'You already have full health.'
            else:
                gold_add(user['_id'], -1000)
                _life_elixir(client, user, thread_id)
                return
        elif slot == 3:
            if gold < amount * 2500:
                reply = 'You can\'t afford that.'
            else:
                gold_add(user['_id'], amount * -2500)
                _hunting_pet(client, user, amount, thread_id)
                return
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
    client.user_health[user_id] = user['Stats']['Health']
    reply = 'Your health has been restored to its maximum!'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def _hunting_pet(client, user, amount, thread_id):
    beast = random_beast()
    delta_rate = beast[1] * beast[2] * amount
    gold_flow_add(user['_id'], delta_rate)
    if amount == 1:
        reply = 'You\'ve bought a ' + str(beast[1]) + '/' + str(beast[2]) + ' ' + beast[0]
        reply += '! It grants you an additional ' + format_num(delta_rate, truncate=True) + ' gold per hour.'
    else:
        reply = 'You\'ve bought ' + str(amount) + ' ' + str(beast[1]) + '/' + str(beast[2]) + ' ' + beast[0]
        reply += 's! They grant you an additional ' + format_num(delta_rate, truncate=True) + ' gold per hour.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)