from fbchat.models import *
from datetime import datetime, timedelta
import random

from data import item_drop_data, monster_data, random_beast
from mongo import *
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
_connect(4, 5, 3)
_connect(5, 2, 2)
# - Sleepywood
_connect(2, 6, 2)
_connect(3, 6, 2)
_connect(4, 6, 2)
_connect(5, 6, 2)
_connect(6, 7, 2)
# - Masteria
_connect(5, 8, 5)
_connect(8, 9, 3)
_connect(9, 10, 3)
# - El Nath
_connect(3, 11, 12)
_connect(11, 12, 6)
_connect(12, 13, 7)
_connect(13, 14, 0)
# - Aqua Road
_connect(11, 15, 10)
_connect(12, 15, 6)
_connect(15, 16, 2)
_connect(15, 22, 5)
# - Ludibrium
_connect(11, 19, 20)
_connect(19, 20, 5)
_connect(20, 21, 1)
_connect(19, 22, 10)
_connect(19, 23, 10)
# - Nihal Desert
_connect(11, 17, 14)
_connect(17, 18, 5)
# - Leafre
#_connect(11, 24, 15)
_connect(24, 25, 5)
_connect(25, 26, 2)
#_connect(24, 27, 30)


def location_features(location):
    return feature_map.get(location, [])


def location_level(location):
    if location in monster_data:
        level_min, level_max = None, None
        for monster_datum in monster_data[location]:
            if 'Level' in monster_datum:
                monster_min, monster_max = monster_datum['Level']
                level_min = monster_min if level_min is None else min(level_min, monster_min)
                level_max = monster_max if level_max is None else max(level_max, monster_max)
            else:
                return None, None
        return level_min, level_max
    else:
        return None


def explore_location(client, user, thread_id):
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
        final_amount = 0
        for _ in range(8):
            amount = 0
            while rate > random.random():
                amount += 1
            final_amount = max(amount, final_amount)
        if final_amount > 0:
            item_drops[item] = final_amount
            inventory_add(user['_id'], item, final_amount)
    while len(item_drops) > 3:
        del item_drops[random.choice(list(item_drops.keys()))]

    # Calculate gold gain
    delta_gold = 50 * (user['GoldFlow'] / 100 + 10)
    delta_gold = int(delta_gold * gold_multiplier * random.uniform(0.8, 1.2))
    gold_add(user['_id'], delta_gold)

    # Check for discovered hunting pet
    beast = None
    delta_flow = 0
    if beast_multiplier > random.random() * 100:
        beast = random_beast()
        delta_flow = beast[1] * beast[2]
        gold_flow_add(user['_id'], delta_flow)

    # Check for discovered location
    current = location_names_reverse[user['Location']]
    progress = user['LocationProgress']
    adjacent = adjacent_locations(user, discovered=False)
    unlocked, presence = None, None
    if len(adjacent) > 0:
        name = location_names[adjacent[0]]
        distance = max(edges[current][adjacent[0]], 1)
        presence = progress.get(name, 0) + random.uniform(1, 2) / distance
        if presence >= 1:
            location_progress_set(user['_id'], name, 1)
            unlocked = name
            presence = progress.get(location_names[adjacent[1]], 0) if len(adjacent) > 1 else None
        else:
            location_progress_set(user['_id'], name, presence)

    # Create message
    reply = []
    line = 'You spent some time exploring ' + location_names[current]
    line += ' and found ' + format_num(delta_gold, truncate=True) + ' gold.'
    reply.append(line)
    if beast:
        line = 'A wild ' + str(beast[1]) + '/' + str(beast[2]) + ' '
        line += beast[0] + ' took a liking to you! It follows you around, '
        line += 'granting you an additional ' + format_num(delta_flow, truncate=True) + ' gold per hour.'
        reply.append(line)
    if unlocked is not None:
        line = 'During this time, you randomly stumbled upon ' + unlocked + '!'
        reply.append(line)
    if presence is not None:
        line = 'On the way back, you sensed the presence of an' + ('other' if unlocked is not None else '')
        line += ' undiscovered location nearby. (' + str(int(presence * 100)) + '% to discovery)'
        reply.append(line)
    reply = ' '.join(reply)
    if len(item_drops) > 0:
        singular = len(item_drops) == 1 and list(item_drops.values())[0] == 1
        reply += '\n\nYou found the following item' + ('' if singular else 's') + ':'
        for item_key in sorted(item_drops.keys(), key=lambda x: item_names_reverse[x]):
            reply += '\n-> ' + item_key + ' x ' + str(item_drops[item_key])

    message = Message(reply)
    client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)


def check_travel(client, user, thread_id):
    current = location_names_reverse[user['Location']]
    if current == 0:
        reply = 'You cannot travel anywhere.'
    else:
        reply = ['You are in ' + location_names[current]]
        reply[0] += ' and can travel to the following places:'
        for i in adjacent_locations(user):
            level_range = location_level(location_names[i])
            line = '-> ' + location_names[i]
            if level_range is not None:
                line += ' (Levels ' + str('???' if level_range[0] is None else level_range[0])
                line += ' - ' + str('???' if level_range[1] is None else level_range[1]) + ')'
            reply.append(line + ': ' + str(edges[current][i]) + ' minutes away')
        if len(reply) > 1:
            reply = '\n'.join(reply)
        else:
            reply = 'You have not discovered any surrounding locations yet.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def travel_to_location(client, user, text, thread_id):
    current = location_names_reverse[user['Location']]
    location = query_location(text, adjacent_locations(user))
    if location is None:
        reply = 'Invalid location.'
    else:
        user_id = user['_id']
        client.user_states[user_id] = (UserState.Travel, {
            'Destination': location_names[location],
            'EndTime': datetime.now() + timedelta(minutes=edges[current][location])
        })
        reply = user['Name'] + ' is now traveling to ' + location_names[location] + '.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def adjacent_locations(user, discovered=True):
    current = location_names_reverse[user['Location']]
    progress = user['LocationProgress']
    locations = []
    for i, time in enumerate(edges[current]):
        if time >= 0 and ((progress.get(location_names[i], 0) >= 1) == discovered):
            locations.append(i)
    return locations


def query_location(query, locations):
    query = query.lower()
    locations = [location_names[location] for location in locations]
    for location in locations:
        if query == location.lower():
            return location_names_reverse[location]
    for location in locations:
        if query in location.lower().split():
            return location_names_reverse[location]
    for location in locations:
        if location.lower().startswith(query):
            return location_names_reverse[location]
    return None