from fbchat.models import *
from datetime import datetime, timedelta
import random

from data import item_drop_data, monster_data, random_beast
from enums import UserState, Region, Item
from mongo import *
from util import *

_edges = {}


def _connect(a, b, time):
    if a not in _edges:
        _edges[a] = {}
    if b not in _edges:
        _edges[b] = {}
    _edges[a][b] = time
    _edges[b][a] = time


# - Victoria Island
_connect(Location['Lith Harbor'], Location['Henesys'], 2)
_connect(Location['Lith Harbor'], Location['Kerning City'], 2)
_connect(Location['Henesys'], Location['Ellinia'], 3)
_connect(Location['Ellinia'], Location['Perion'], 3)
_connect(Location['Perion'], Location['Kerning City'], 3)
_connect(Location['Kerning City'], Location['Henesys'], 2)
# - Sleepywood
_connect(Location['Henesys'], Location['Sleepywood'], 2)
_connect(Location['Ellinia'], Location['Sleepywood'], 2)
_connect(Location['Perion'], Location['Sleepywood'], 2)
_connect(Location['Kerning City'], Location['Sleepywood'], 2)
_connect(Location['Sleepywood'], Location['Cursed Sanctuary'], 2)
# - Masteria
_connect(Location['Kerning City'], Location['New Leaf City'], 5)
_connect(Location['New Leaf City'], Location['Krakian Jungle'], 3)
_connect(Location['New Leaf City'], Location['Bigger Ben'], 3)
# - El Nath Mountains
_connect(Location['Ellinia'], Location['Orbis'], 12)
_connect(Location['Orbis'], Location['El Nath'], 6)
_connect(Location['El Nath'], Location['Dead Mine'], 7)
_connect(Location['Dead Mine'], Location['Zakum\'s Altar'], 2)
# - Aqua Road
_connect(Location['Orbis'], Location['Aqua Road'], 10)
_connect(Location['El Nath'], Location['Aqua Road'], 6)
_connect(Location['Aqua Road'], Location['Cave of Pianus'], 2)
_connect(Location['Aqua Road'], Location['Korean Folk Town'], 5)
# - Ludus Lake
_connect(Location['Orbis'], Location['Ludibrium'], 20)
_connect(Location['Ludibrium'], Location['Path of Time'], 5)
_connect(Location['Path of Time'], Location['Papulatus Clock Tower'], 1)
_connect(Location['Ludibrium'], Location['Korean Folk Town'], 10)
_connect(Location['Ludibrium'], Location['Omega Sector'], 10)
# - Nihal Desert
_connect(Location['Orbis'], Location['Ariant'], 14)
_connect(Location['Ariant'], Location['Magatia'], 5)
# - Leafre
#_connect(Location['Orbis'], Location['Leafre'], 15)
_connect(Location['Leafre'], Location['Minar Forest'], 5)
_connect(Location['Minar Forest'], Location['Horntail\'s Lair'], 2)
#_connect(Location['Leafre'], Location['Temple of Time'], 30)

_feature_map = {
    Location['Lith Harbor']: ['Shop'],
    Location['Henesys']: ['Crafting', 'Shop'],
    Location['Ellinia']: ['Crafting', 'Shop'],
    Location['Perion']: ['Crafting', 'Shop'],
    Location['Kerning City']: ['Shop'],
    Location['Sleepywood']: ['Crafting', 'Shop'],
    Location['New Leaf City']: ['Shop'],
    Location['Orbis']: ['Crafting', 'Shop'],
    Location['El Nath']: ['Crafting', 'Shop'],
    Location['Ariant']: ['Crafting', 'Shop'],
    Location['Magatia']: ['Crafting', 'Shop'],
    Location['Ludibrium']: ['Crafting', 'Shop'],
    Location['Korean Folk Town']: ['Crafting', 'Shop'],
    Location['Omega Sector']: ['Crafting', 'Shop'],
    Location['Leafre']: ['Crafting', 'Shop'],
}

_region_map = {
    Location['Maple Island']: Region.MAPLE_ISLAND,
    Location['Lith Harbor']: Region.VICTORIA_ISLAND,
    Location['Henesys']: Region.VICTORIA_ISLAND,
    Location['Ellinia']: Region.VICTORIA_ISLAND,
    Location['Perion']: Region.VICTORIA_ISLAND,
    Location['Kerning City']: Region.VICTORIA_ISLAND,
    Location['Sleepywood']: Region.SLEEPYWOOD,
    Location['Cursed Sanctuary']: Region.SLEEPYWOOD,
    Location['New Leaf City']: Region.MASTERIA,
    Location['Krakian Jungle']: Region.MASTERIA,
    Location['Bigger Ben']: Region.MASTERIA,
    Location['Orbis']: Region.EL_NATH_MOUNTAINS,
    Location['El Nath']: Region.EL_NATH_MOUNTAINS,
    Location['Dead Mine']: Region.DEAD_MINE,
    Location['Zakum\'s Altar']: Region.DEAD_MINE,
    Location['Aqua Road']: Region.AQUA_ROAD,
    Location['Cave of Pianus']: Region.AQUA_ROAD,
    Location['Ariant']: Region.NIHAL_DESERT,
    Location['Magatia']: Region.NIHAL_DESERT,
    Location['Ludibrium']: Region.LUDUS_LAKE,
    Location['Path of Time']: Region.CLOCK_TOWER,
    Location['Papulatus Clock Tower']: Region.CLOCK_TOWER,
    Location['Korean Folk Town']: Region.LUDUS_LAKE,
    Location['Omega Sector']: Region.LUDUS_LAKE,
    Location['Leafre']: Region.MINAR_FOREST,
    Location['Minar Forest']: Region.MINAR_FOREST,
    Location['Horntail\'s Lair']: Region.MINAR_FOREST,
    Location['Temple of Time']: Region.TEMPLE_OF_TIME,
}


def location_features(location):
    return _feature_map.get(Location[location], [])


def location_region(location):
    return _region_map.get(Location[location], None)


def location_level(location):
    location = Location[location].name
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
    location = Location[user['Location']]

    # Apply location specific modifiers
    gold_multiplier = 1
    beast_multiplier = 1
    if location == Location['Maple Island']:
        gold_multiplier = 0
        beast_multiplier = 0
    elif location == Location['Lith Harbor']:
        gold_multiplier = 0.5
    elif location == Location['Henesys']:
        beast_multiplier = 3
    elif location == Location['New Leaf City']:
        gold_multiplier = 2
        beast_multiplier = 0
    elif location == Location['Krakian Jungle']:
        beast_multiplier = 5

    # Calculate item drops
    item_drops = {}
    for item, rate in item_drop_data.get(location.name, {}).items():
        amount = 0
        for _ in range(int(rate * 10)):
            while random.random() < 0.1:
                amount += 1
        if amount > 0:
            item_drops[item] = amount
            inventory_add(user['_id'], item, amount)
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
    current = Location[user['Location']]
    progress = user['LocationProgress']
    adjacent = adjacent_locations(user, discovered=False)
    unlocked, presence = None, None
    if len(adjacent) > 0:
        location = Location[adjacent[0]]
        distance = max(_edges[current][location], 1)
        presence = progress.get(location.name, 0) + random.uniform(1, 2) / distance
        if presence >= 1:
            location_progress_set(user['_id'], location.name, 1)
            unlocked = location.name
            presence = progress.get(adjacent[1], 0) if len(adjacent) > 1 else None
        else:
            location_progress_set(user['_id'], location.name, presence)

    # Create message
    reply = []
    line = 'You spent some time exploring ' + current.name
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
        for item_key in sorted(item_drops.keys(), key=lambda x: Item[x].value):
            reply += '\n-> ' + item_key + ' x ' + str(item_drops[item_key])

    message = Message(reply)
    client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)


def check_travel(client, user, thread_id):
    current = Location[user['Location']]
    if current == Location['Maple Island']:
        reply = 'You cannot travel anywhere.'
    else:
        reply = ['You are in ' + current.name + ' and can travel to the following places:']
        for location in adjacent_locations(user):
            level_range = location_level(location)
            line = '-> ' + location
            if level_range is not None:
                line += ' (Levels ' + str('???' if level_range[0] is None else level_range[0])
                line += ' - ' + str('???' if level_range[1] is None else level_range[1]) + ')'
            reply.append(line + ': ' + str(_edges[current][Location[location]]) + ' minutes away')
        if len(reply) > 1:
            reply = '\n'.join(reply)
        else:
            reply = 'You have not discovered any surrounding locations yet.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def travel_to_location(client, user, text, thread_id):
    current = Location[user['Location']]
    location = query_location(text, adjacent_locations(user))
    if location is None:
        reply = 'Invalid location.'
    else:
        user_id = user['_id']
        client.user_states[user_id] = (UserState.TRAVEL, {
            'Destination': location,
            'EndTime': datetime.now() + timedelta(minutes=_edges[current][Location[location]])
        })
        reply = user['Name'] + ' is now traveling to ' + location + '.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def adjacent_locations(user, discovered=True):
    current = Location[user['Location']]
    progress = user['LocationProgress']
    locations = []
    for location, time in _edges[current].items():
        if time >= 0 and ((progress.get(location.name, 0) >= 1) == discovered):
            locations.append(location.name)
    return locations


def query_location(query, locations=Location.__members__.keys()):
    query = query.lower()
    locations = [Location[location].name for location in locations]
    for location in locations:
        if query == location.lower():
            return location
    for location in locations:
        if query in location.lower().split():
            return location
    for location in locations:
        if location.lower().startswith(query):
            return location
    return None