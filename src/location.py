from fbchat.models import *
from datetime import datetime, timedelta
import random

from data import item_drop_data, monster_data, random_beast
from enums import UserState, Region, Item
from mongo import *
from util import *

_edges = {location: {} for location in Location.__members__.values()}


def _connect(a, b, time):
    _edges[a][b] = time
    _edges[b][a] = time


# Victoria Island
_connect(Location['Lith Harbor'], Location['Henesys'], 2)
_connect(Location['Lith Harbor'], Location['Kerning City'], 2)
_connect(Location['Henesys'], Location['Ellinia'], 3)
_connect(Location['Ellinia'], Location['Perion'], 3)
_connect(Location['Perion'], Location['Kerning City'], 3)
_connect(Location['Kerning City'], Location['Henesys'], 2)
# Sleepywood
_connect(Location['Henesys'], Location['Sleepywood'], 2)
_connect(Location['Ellinia'], Location['Sleepywood'], 2)
_connect(Location['Perion'], Location['Sleepywood'], 2)
_connect(Location['Kerning City'], Location['Sleepywood'], 2)
_connect(Location['Sleepywood'], Location['Silent Swamp'], 2)
_connect(Location['Sleepywood'], Location['Drake Cave'], 3)
_connect(Location['Drake Cave'], Location['Temple Entrance'], 2)
_connect(Location['Temple Entrance'], Location['Cursed Sanctuary'], 2)
# Masteria
_connect(Location['Kerning City'], Location['New Leaf City'], 6)
_connect(Location['New Leaf City'], Location['Krakian Jungle'], 4)
_connect(Location['New Leaf City'], Location['Meso Gears Tower'], 2)
# El Nath Mountains
_connect(Location['Ellinia'], Location['Orbis'], 12)
_connect(Location['Orbis'], Location['Cloud Park'], 4)
_connect(Location['Cloud Park'], Location['Garden of Colors'], 4)
_connect(Location['Orbis'], Location['Orbis Tower'], 3)
_connect(Location['Orbis Tower'], Location['El Nath'], 5)
_connect(Location['El Nath'], Location['Ice Valley'], 3)
# Dead Mine
_connect(Location['Ice Valley'], Location['Sharp Cliffs'], 4)
_connect(Location['Sharp Cliffs'], Location['Dead Mine'], 4)
_connect(Location['Dead Mine'], Location['Caves of Trial'], 2)
_connect(Location['Caves of Trial'], Location['Altar of Flame'], 2)
# Aqua Road
_connect(Location['Coral Forest'], Location['Orbis Tower'], 8)
_connect(Location['Coral Forest'], Location['Aquarium'], 3)
_connect(Location['Coral Forest'], Location['Wrecked Ship Grave'], 6)
_connect(Location['Seaweed Road'], Location['Aquarium'], 3)
_connect(Location['Seaweed Road'], Location['Wrecked Ship Grave'], 6)
_connect(Location['Seaweed Road'], Location['Korean Folk Town'], 4)
_connect(Location['Wrecked Ship Grave'], Location['Deepest Cave'], 2)
# Nihal Desert
_connect(Location['Orbis'], Location['Ariant'], 14)
_connect(Location['Ariant'], Location['Burning Sands'], 3)
_connect(Location['Ariant'], Location['Sunset Road'], 5)
_connect(Location['Sunset Road'], Location['Magatia'], 5)
_connect(Location['Magatia'], Location['Zenumist Laboratory'], 2)
_connect(Location['Magatia'], Location['Alcadno Laboratory'], 2)
_connect(Location['Zenumist Laboratory'], Location['Alcadno Laboratory'], 2)
# Ludus Lake
_connect(Location['Orbis'], Location['Ludibrium'], 20)
_connect(Location['Ludibrium'], Location['Toy Factory'], 2)
_connect(Location['Ludibrium'], Location['Eos Tower'], 3)
_connect(Location['Ludibrium'], Location['Helios Tower'], 3)
# Clock Tower
_connect(Location['Toy Factory'], Location['Path of Time'], 4)
_connect(Location['Path of Time'], Location['Warped Passage'], 3)
_connect(Location['Path of Time'], Location['Forgotten Passage'], 3)
_connect(Location['Warped Passage'], Location['Clock Tower Origin'], 2)
_connect(Location['Forgotten Passage'], Location['Clock Tower Origin'], 2)
# Korean Folk Town
_connect(Location['Eos Tower'], Location['Korean Folk Town'], 12)
_connect(Location['Korean Folk Town'], Location['Black Mountain'], 6)
_connect(Location['Black Mountain'], Location['Goblin Ridge'], 4)
# Omega Sector
_connect(Location['Helios Tower'], Location['Omega Sector'], 12)
_connect(Location['Omega Sector'], Location['Boswell Field'], 6)
_connect(Location['Boswell Field'], Location['Mothership Interior'], 4)
# Leafre
_connect(Location['Leafre'], Location['Forest Valley'], 6)
_connect(Location['Forest Valley'], Location['Dragon Forest'], 3)
_connect(Location['Dragon Forest'], Location['Dragon Canyon'], 5)
_connect(Location['Dragon Canyon'], Location['Cave of Life'], 2)

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
    Location['Aquarium']: ['Shop'],
    Location['Ludibrium']: ['Crafting', 'Shop'],
    Location['Korean Folk Town']: ['Crafting', 'Shop'],
    Location['Omega Sector']: ['Crafting', 'Shop'],
    Location['Leafre']: ['Crafting', 'Shop'],
    Location['Ariant']: ['Crafting', 'Shop'],
    Location['Magatia']: ['Crafting', 'Shop']
}

_region_map = {
    Location['Maple Island']: Region.MAPLE_ISLAND,
    Location['Lith Harbor']: Region.VICTORIA_ISLAND,
    Location['Henesys']: Region.VICTORIA_ISLAND,
    Location['Ellinia']: Region.VICTORIA_ISLAND,
    Location['Perion']: Region.VICTORIA_ISLAND,
    Location['Kerning City']: Region.VICTORIA_ISLAND,
    Location['Sleepywood']: Region.SLEEPYWOOD,
    Location['Silent Swamp']: Region.SLEEPYWOOD,
    Location['Drake Cave']: Region.SLEEPYWOOD,
    Location['Temple Entrance']: Region.SLEEPYWOOD,
    Location['Cursed Sanctuary']: Region.SLEEPYWOOD,
    Location['New Leaf City']: Region.MASTERIA,
    Location['Meso Gears Tower']: Region.MASTERIA,
    Location['Krakian Jungle']: Region.MASTERIA,
    Location['Alien Base']: Region.MASTERIA,
    Location['Orbis']: Region.EL_NATH_MOUNTAINS,
    Location['Cloud Park']: Region.EL_NATH_MOUNTAINS,
    Location['Garden of Colors']: Region.EL_NATH_MOUNTAINS,
    Location['Orbis Tower']: Region.EL_NATH_MOUNTAINS,
    Location['El Nath']: Region.EL_NATH_MOUNTAINS,
    Location['Ice Valley']: Region.EL_NATH_MOUNTAINS,
    Location['Sharp Cliffs']: Region.DEAD_MINE,
    Location['Dead Mine']: Region.DEAD_MINE,
    Location['Caves of Trial']: Region.DEAD_MINE,
    Location['Altar of Flame']: Region.DEAD_MINE,
    Location['Aquarium']: Region.AQUA_ROAD,
    Location['Coral Forest']: Region.AQUA_ROAD,
    Location['Seaweed Road']: Region.AQUA_ROAD,
    Location['Wrecked Ship Grave']: Region.AQUA_ROAD,
    Location['Deepest Cave']: Region.AQUA_ROAD,
    Location['Ludibrium']: Region.LUDUS_LAKE,
    Location['Toy Factory']: Region.LUDUS_LAKE,
    Location['Helios Tower']: Region.LUDUS_LAKE,
    Location['Eos Tower']: Region.LUDUS_LAKE,
    Location['Path of Time']: Region.CLOCK_TOWER,
    Location['Warped Passage']: Region.CLOCK_TOWER,
    Location['Forgotten Passage']: Region.CLOCK_TOWER,
    Location['Clock Tower Origin']: Region.CLOCK_TOWER,
    Location['Korean Folk Town']: Region.KOREAN_FOLK_TOWN,
    Location['Black Mountain']: Region.KOREAN_FOLK_TOWN,
    Location['Goblin Ridge']: Region.KOREAN_FOLK_TOWN,
    Location['Omega Sector']: Region.OMEGA_SECTOR,
    Location['Boswell Field']: Region.OMEGA_SECTOR,
    Location['Mothership Interior']: Region.OMEGA_SECTOR,
    Location['Leafre']: Region.MINAR_FOREST,
    Location['Forest Valley']: Region.MINAR_FOREST,
    Location['Dragon Forest']: Region.MINAR_FOREST,
    Location['Dragon Canyon']: Region.MINAR_FOREST,
    Location['Cave of Life']: Region.MINAR_FOREST,
    Location['Ariant']: Region.NIHAL_DESERT,
    Location['Burning Sands']: Region.NIHAL_DESERT,
    Location['Sunset Road']: Region.NIHAL_DESERT,
    Location['Magatia']: Region.NIHAL_DESERT,
    Location['Zenumist Laboratory']: Region.NIHAL_DESERT,
    Location['Alcadno Laboratory']: Region.NIHAL_DESERT,
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
        presence = progress.get(location.name, 0) + random.uniform(0.5, 1) / distance
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
    features = location_features(current.name)
    level_range = location_level(current.name)

    reply = 'Welcome to ' + current.name + '! '
    if level_range is None:
        reply += 'There are no monsters here. '
    elif level_range == (None, None):
        reply += 'The monsters here scale to your level. '
    else:
        reply += 'The monsters here are levels ' + str(level_range[0])
        reply += ' to ' + str(level_range[1]) + '. '
    if features:
        reply += 'The following services are available here:'
        for feature in features:
            reply += '\n-> ' + feature
    else:
        reply += 'There are no services available here.'

    if current == Location['Maple Island']:
        reply += '\n\nYou cannot travel anywhere.'
    else:
        adjacent = adjacent_locations(user)
        if len(adjacent):
            reply += '\n\nYou are in ' + current.name + ' and can travel to the following places:'
            for location in adjacent:
                level_range = location_level(location)
                reply += '\n-> ' + location
                if level_range is not None:
                    reply += ' (Levels ' + str('???' if level_range[0] is None else level_range[0])
                    reply += ' - ' + str('???' if level_range[1] is None else level_range[1]) + ')'
                reply += ': ' + str(_edges[current][Location[location]]) + ' minutes away'
        else:
            reply += '\n\nYou have not discovered any surrounding locations yet.'
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