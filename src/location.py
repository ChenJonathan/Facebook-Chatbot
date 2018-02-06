from fbchat.models import *
from datetime import datetime, timedelta
import math
import string

from mongo import *

names = ['Maple Island', 'Lith Harbor', 'Henesys', 'Ellinia', 'Perion', 'Kerning City']
names += ['Sleepywood', 'Cursed Sanctuary', 'New Leaf City', 'Krakian Jungle', 'Bigger Ben']
names += ['Orbis', 'El Nath', 'Dead Mine', 'Zakum\'s Altar', 'Aqua Road', 'Cave of Pianus']
names += ['Ludibrium', 'Path of Time', 'Papulatus Tower', 'Korean Folk Town', 'Omega Sector']
names += ['Nihal Desert', 'Magatia', 'Leafre', 'Minar Forest', 'Cave of Life', 'Temple of Time']

edges = [[-1 for _ in range(len(names))] for _ in range(len(names))]

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
_connect(3, 11, 18)
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

def location_to_name(location):
    return names[location] if location >= 0 and location < len(names) else None

def name_to_location(text):
    print(text)
    text = text.lower()
    for i, name in enumerate(names):
        name = name.strip().lower().split()
        if text in name:
            return i
    return None

def check_locations(client, user, thread_id):
    current = user['location']
    reply = ['You are in ' + names[current] + ' and can travel to the following places:']
    for i, time in enumerate(edges[current]):
        if time >= 0 and i in user['locations_discovered']:
            reply.append('- ' + names[i] + ': ' + str(time) + ' minutes away')
    reply = '\n'.join(reply) if reply else 'You cannot travel anywhere.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def travel_to_location(client, user, text, thread_id):
    current = user['location']
    location = name_to_location(text)
    if location == None:
        reply = 'That location doesn\'t exist.'
    elif edges[current][location] < 0 or location not in user['locations_discovered']:
        reply = 'You cannot travel there.'
    else:
        record = (location, datetime.now() + timedelta(minutes=edges[current][location]))
        client.travel_record[user['_id']] = record
        reply = user['name'] + ' is now traveling to ' + names[location] + '.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def grant_treasures(client, user, elapsed, thread_id):
    message = Message('You have explored for ' + str(elapsed) + ' minutes!')
    client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)