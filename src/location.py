from fbchat.models import *
import random

from data import item_drop_data, random_beast
from mongo import *
from travel import edges, adjacent_locations
from util import *

feature_map = {
    'Lith Harbor': ['Shop'],
    'Henesys': ['Crafting', 'Shop'],
    'Ellinia': ['Crafting', 'Shop'],
    'Perion': ['Crafting', 'Crafting', 'Shop'],
    'Kerning City': ['Shop'],
    'Sleepywood': ['Crafting', 'Shop'],
    'New Leaf City': ['Gambling - Coming soon!', 'Shop'],
    'Orbis': ['Crafting', 'Shop'],
    'El Nath': ['Crafting', 'Shop'],
    'Ariant': ['Crafting', 'Shop'],
    'Magatia': ['Crafting', 'Shop'],
    'Ludibrium': ['Crafting', 'Shop'],
    'Korean Folk Town': ['Crafting', 'Shop'],
    'Omega Sector': ['Crafting', 'Shop'],
    'Leafre': ['Crafting', 'Shop'],
}


def location_features(location):
    return feature_map.get(location, [])


def explore_location(client, user, thread_id):
    seed = random.uniform(0.8, 1.2)
    location = location_names_reverse[user['Location']]

    # Apply location specific modifiers
    gold_multiplier = 1
    beast_multiplier = 1
    if location == 0:
        gold_multiplier = 0
        beast_multiplier = 0
    elif location == 1:
        gold_multiplier = 0.5
    elif location == 2:
        beast_multiplier = 3
    elif location == 8:
        gold_multiplier = 2
        beast_multiplier = 0
    elif location == 9:
        beast_multiplier = 5

    # Calculate item drops
    item_drops = {}
    for item, rate in item_drop_data.get(user['Location'], {}).items():
        trials = []
        for _ in range(8):
            amount = 0
            while rate > random.random():
                amount += 1
            trials.append(amount)
        final_amount = sorted(trials)[-2]
        if final_amount > 0:
            item_drops[item] = final_amount
            inventory_add(user['_id'], item, final_amount)

    # Calculate gold gain
    delta_gold = 50 * (user['GoldFlow'] / 100 + 10)
    delta_gold = int(delta_gold * seed * gold_multiplier * random.uniform(0.8, 1.2))
    gold_add(user['_id'], delta_gold)

    # Check for discovered hunting pet
    beast = None
    delta_rate = 0
    if seed / 100 * beast_multiplier > random.random():
        beast = random_beast()
        delta_rate = beast[1] * beast[2]
        gold_rate_add(user['_id'], delta_rate)

    # Check for discovered location
    current = location_names_reverse[user['Location']]
    progress = user['LocationProgress']
    unlocked = []
    presence = False
    for i in adjacent_locations(user, discovered=False):
        if edges[current][i] > 0:
            new_progress = progress.get(location_names[i], 0) + seed * 2 / edges[current][i]
        else:
            new_progress = 1
        if new_progress >= 1:
            location_progress_set(user['_id'], location_names[i], 1)
            unlocked.append(i)
        else:
            location_progress_set(user['_id'], location_names[i], new_progress)
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
        singular = len(item_drops) == 1 and list(item_drops.values())[0] == 1
        reply += '\n\nYou found the following item' + ('' if singular else 's') + ':'
        for item, amount in item_drops.items():
            reply += '\n-> ' + item + ' x ' + str(amount)

    message = Message(reply)
    client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)