from fbchat.models import *
from datetime import datetime, timedelta
import math
import string

from mongo import *

names = ['Plains', 'Desert', 'Swamp', 'Forest', 'Mountains']
edges = [
    [-1,  2, -1,  3, -1],
    [ 2, -1, -1, -1,  2],
    [-1, -1, -1,  4, -1],
    [ 3, -1,  4, -1,  3],
    [-1,  2, -1,  3, -1]
]

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
    reply = ['You can travel to the following places:']
    for i, time in enumerate(edges[current]):
        if time >= 0:
            reply.append(names[i] + ': ' + str(time) + ' minutes away')
    reply = '\n'.join(reply) if reply else 'You cannot travel anywhere.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

def travel_to_location(client, user, text, thread_id):
    current = user['location']
    location = name_to_location(text)
    if user['_id'] in client.travel_record:
        record = client.travel_record[user['_id']]
        minutes = math.ceil((record[1] - datetime.now()).total_seconds() / 60)
        reply = 'You\'re busy traveling to ' + location_to_name(record[0])
        reply += '. (' + str(minutes) + ' minutes remaining)'
    elif location == None:
        reply = 'That location doesn\'t exist.'
    elif edges[current][location] < 0:
        reply = 'You cannot travel there.'
    else:
        record = (location, datetime.now() + timedelta(minutes=edges[current][location]))
        client.travel_record[user['_id']] = record
        reply = user['name'] + ' is now traveling to ' + names[location] + '.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)