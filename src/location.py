from fbchat.models import *
from datetime import datetime, timedelta
import math
import random
import string

from hearthstone import random_beast
from mongo import *
from util import location_names, name_to_location

edges = [[-1 for _ in range(len(location_names))] for _ in range(len(location_names))]

def _connect(a, b, time):
    edges[a][b] = time
    edges[b][a] = time

# - Lith Harbor
_connect(1, 2, 2)
_connect(1, 5, 2)
# - Victoria Island
_connect(2, 3, 3)
_connect(3, 4, 3)
_connect(4, 5, 2)
_connect(5, 2, 2)
# - Sleepywood
_connect(2, 6, 4)
_connect(3, 6, 4)
_connect(4, 6, 4)
_connect(5, 6, 4)
_connect(6, 7, 5)
# - New Leaf City
_connect(5, 8, 8)
_connect(8, 9, 5)
_connect(9, 10, 5)
# - El Nath
# _connect(3, 11, 18)
_connect(11, 12, 6)
_connect(12, 13, 9)
_connect(13, 14, 0)
# - Aqua Road
_connect(11, 15, 10)
_connect(12, 15, 7)
_connect(15, 16, 0)
_connect(15, 20, 4)
# - Ludibrium
_connect(11, 17, 16)
_connect(17, 18, 5)
_connect(18, 19, 0)
_connect(17, 20, 9)
_connect(17, 21, 10)
# - Nihal Desert
_connect(11, 22, 12)
_connect(22, 23, 5)
# - Leafre
_connect(11, 24, 15)
_connect(24, 25, 5)
_connect(25, 26, 0)
_connect(24, 27, 60)

def check_locations(client, user, thread_id):
    current = user['location']
    if current == 0:
        reply = 'You cannot travel anywhere.'
    else:
        progress_keys = user['location_progress'].keys()
        reply = ['You are in ' + location_names[current]]
        reply[0] += ' and can travel to the following places:'
        for i, time in enumerate(edges[current]):
            if time >= 0 and str(i) not in progress_keys:
                reply.append('- ' + location_names[i] + ': ' + str(time) + ' minutes away')
        if len(reply) > 1:
            reply = '\n'.join(reply)
        else:
            reply = 'You have not discovered any surrounding locations yet.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def travel_to_location(client, user, text, thread_id):
    current = user['location']
    progress_keys = user['location_progress'].keys()
    location = name_to_location(text)
    if location == None:
        reply = 'That location doesn\'t exist.'
    elif edges[current][location] < 0 or str(location) in progress_keys:
        reply = 'You cannot travel there.'
    else:
        record = (location, datetime.now() + timedelta(minutes=edges[current][location]))
        client.travel_record[user['_id']] = record
        reply = user['name'] + ' is now traveling to ' + location_names[location] + '.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def explore_location(client, user, thread_id):
    seed = random.uniform(0.8, 1.2)
    location = user['location']

    # Apply location specific modifiers
    gold_multiplier = 1
    beast_multiplier = 1
    item_drop_rates = {}
    if location == 0:
        gold_multiplier = 0
        beast_multiplier = 0
    elif location == 1:
        gold_multiplier = 0.5
        item_drop_rates['Bottled Light'] = 0.1
    elif location == 2:
        beast_multiplier = 3
        item_drop_rates['Wild Essence'] = 0.7
    elif location == 3:
        item_drop_rates['Arcane Essence'] = 0.7
        item_drop_rates['Breathing Wood'] = 0.5
    elif location == 4:
        item_drop_rates['Brutal Essence'] = 0.7
        item_drop_rates['Drop of Earth'] = 0.2
        item_drop_rates['Iron Shard'] = 0.5
    elif location == 5:
        item_drop_rates['Void Essence'] = 0.7
        item_drop_rates['Bottled Darkness'] = 0.1
    elif location == 6:
        beast_multiplier = 0
        item_drop_rates['Breathing Wood'] = 0.5
        item_drop_rates['Shifting Vines'] = 0.2
    elif location == 7:
        beast_multiplier = 0
        item_drop_rates['Arcane Essence'] = 0.3
        item_drop_rates['Void Essence'] = 0.3
        item_drop_rates['Bottled Darkness'] = 0.2
        item_drop_rates['Touch of Death'] = 0.1
        item_drop_rates['Warped Bones'] = 0.2
    elif location == 8:
        gold_multiplier = 2
        beast_multiplier = 0
    elif location == 9:
        beast_multiplier = 5
        item_drop_rates['Breathing Wood'] = 0.5
        item_drop_rates['Shifting Vines'] = 0.5
    elif location == 10:
        item_drop_rates['Howling Wind'] = 0.1
        item_drop_rates['Clockwork Shard'] = 0.6
        item_drop_rates['Time Shard'] = 0.1
    elif location == 11:
        pass
    elif location == 12:
        pass
    elif location == 13:
        pass
    elif location == 14:
        pass
    elif location == 15:
        pass
    elif location == 16:
        pass
    elif location == 17:
        pass
    elif location == 18:
        pass
    elif location == 19:
        pass
    elif location == 20:
        pass
    elif location == 21:
        pass
    elif location == 22:
        pass
    elif location == 23:
        pass
    elif location == 24:
        pass
    elif location == 25:
        pass
    elif location == 26:
        pass
    elif location == 27:
        pass

    # Calculate item drops
    item_drops = {}
    for item, rate in item_drop_rates.items():
        trials = []
        for _ in range(10):
            amount = 0
            while rate > random.random():
                amount += 1
            trials.append(amount)
        final_amount = sorted(trials)[-2]
        if final_amount > 0:
            item_drops[item] = final_amount
            inventory_add(user['_id'], item, final_amount)

    # Calculate gold gain
    delta_gold = int(seed * (100 + random.randint(-10, 10)) * gold_multiplier)
    gold_add(user['_id'], delta_gold)

    # Check for discovered hunting pet
    beast = None
    if seed / 100 * beast_multiplier > random.random():
        beast = random_beast()
        delta_rate = beast[1] * beast[2]
        gold_rate_add(user['_id'], delta_rate)

    # Check for discovered location
    current = user['location']
    progress = user['location_progress']
    progress_keys = progress.keys()
    unlocked = []
    presence = False
    for i, time in enumerate(edges[current]):
        if time >= 0 and str(i) in progress_keys:
            if edges[current][i] > 0:
                delta_progress = seed / edges[current][i]
                total_progress = progress[str(i)] + delta_progress
            else:
                total_progress = 1
            if total_progress >= 1:
                location_discover(user['_id'], i)
                unlocked.append(i)
            else:
                location_progress_set(user['_id'], i, total_progress)
                presence = True

    # Create message
    reply = []
    line = 'You spent some time exploring ' + location_names[current]
    line += ' and found ' + str(delta_gold) + ' gold.'
    reply.append(line)
    if beast:
        line = 'A wild ' + str(beast[1]) + '/' + str(beast[2]) + ' '
        line += beast[0] + ' took a liking to you! It follows you around, '
        line += 'granting you an additional ' + str(delta_rate) + ' gold per hour.'
        reply.append(line)
    if len(unlocked) > 0:
        line = 'During this time, you randomly stumbled upon '
        line += ' and '.join([location_names[new] for new in unlocked]) + '!'
        reply.append(line)
    if presence:
        line = 'On the way back, you sensed the presence of an'
        line += ('other' if unlocked else '') + ' undiscovered location nearby.'
        reply.append(line)
    reply = ' '.join(reply)
    if len(item_drops) > 0:
        singular = len(item_drops) == 1 and item_drops.values()[0] == 1
        reply += '\n\nYou found the following item' + ('' if singular else 's') + ':'
        for item, amount in item_drops.items():
            reply += '\n-> ' + item + ' x ' + str(amount)

    message = Message(reply)
    client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)