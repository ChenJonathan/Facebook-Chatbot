from fbchat.models import *
import random

from data import beast_data
from mongo import *
from util import *


def generate_shop_info(client, user, thread_id):
    gold = user['Gold']
    damaged = client.user_health.get(user['_id'], base_health(user)) < base_health(user)
    talent_cost = 10000 * 10 ** user['Flags'].get('PurchasedTalents', 0)

    reply = 'Shop information has been sent to you. Check your private messages (or message requests).'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = '<<The Wong Shoppe>>\n'
    reply += 'Buy things with "!shop <slot> <amount>" in a group chat. <amount> defaults to 1 if left blank.\n\n'
    reply += '1. Charity donation: 100 gold (' + str(max(gold // 100, 0)) + ' max)\n'
    reply += '-> Donates a small amount of gold to your local charity.\n\n'
    reply += '2. Night of rest: 1000 gold (' + str(int(gold >= 1000 and damaged)) + ' max)\n'
    reply += '-> Restores your life to its maximum.\n\n'
    reply += '3. Hunting beast: 2500 gold (' + str(max(gold // 2500, 0)) + ' max)\n'
    reply += '-> Hunts monsters for you, granting some gold every hour.\n\n'
    reply += '4. Self awakening: ' + format_num(talent_cost, truncate=True)
    reply += ' gold (' + str(int(gold >= talent_cost)) + ' max)\n'
    reply += '-> Grants you a talent point, which can be spent with "!talent". Cost multiplies by 10 each purchase.'
    client.send(Message(reply), thread_id=user['_id'])


def shop_purchase(client, user, slot, amount, thread_id):
    gold = user['Gold']
    if amount < 1:
        reply = 'Invalid purchase amount.'
    elif slot == 1:
        if gold < amount * 100:
            reply = 'You can\'t afford that.'
        else:
            gold_add(user['_id'], amount * -100)
            _charity_donation(client, thread_id)
            return
    elif slot == 2:
        if amount > 1:
            reply = 'You can\'t rest for multiple nights at once.'
        elif gold < 1000:
            reply = 'You can\'t afford that.'
        elif client.user_health.get(user['_id'], base_health(user)) == base_health(user):
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
    elif slot == 4:
        talent_cost = 10000 * 10 ** user['Flags'].get('PurchasedTalents', 0)
        if amount > 1:
            reply = 'You can\'t awaken multiple times at once.'
        elif gold < talent_cost:
            reply = 'You can\'t afford that.'
        else:
            gold_add(user['_id'], -talent_cost)
            _self_awakening(client, user, thread_id)
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
    client.user_health[user_id] = base_health(user)
    reply = 'Your health has been restored to its maximum!'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def _hunting_pet(client, user, amount, thread_id):
    beast = random.choice(beast_data)
    delta_rate = beast[1] * beast[2] * amount
    gold_flow_add(user['_id'], delta_rate)
    if amount == 1:
        reply = 'You\'ve bought a ' + str(beast[1]) + '/' + str(beast[2]) + ' ' + beast[0]
        reply += '! It grants you an additional ' + format_num(delta_rate, truncate=True) + ' gold per hour.'
    else:
        reply = 'You\'ve bought ' + str(amount) + ' ' + str(beast[1]) + '/' + str(beast[2]) + ' ' + beast[0]
        reply += 's! They grant you an additional ' + format_num(delta_rate, truncate=True) + ' gold per hour.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def _self_awakening(client, user, thread_id):
    talent_cost = 100000 * 10 ** user['Flags'].get('PurchasedTalents', 0)
    talent_purchase(user['_id'], 1)
    reply = 'You\'ve been awakened, granting you a talent point! Spend it with "!talent". '
    reply += 'Your next talent will cost you ' + format_num(talent_cost, truncate=True) + ' gold.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)