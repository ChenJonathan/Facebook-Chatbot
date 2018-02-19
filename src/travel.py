from fbchat.models import *
from datetime import datetime, timedelta

from util import *

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
# - New Leaf City
_connect(5, 8, 5)
_connect(8, 9, 3)
_connect(9, 10, 3)
# - El Nath
# _connect(3, 11, 18)
_connect(11, 12, 6)
_connect(12, 13, 7)
_connect(13, 14, 0)
# - Aqua Road
#_connect(11, 15, 10)
_connect(12, 15, 6)
_connect(15, 16, 2)
_connect(15, 20, 5)
# - Ludibrium
#_connect(11, 17, 16)
_connect(17, 18, 5)
_connect(18, 19, 1)
_connect(17, 20, 8)
_connect(17, 21, 9)
# - Nihal Desert
#_connect(11, 22, 12)
_connect(22, 23, 5)
# - Leafre
#_connect(11, 24, 15)
_connect(24, 25, 5)
_connect(25, 26, 2)
#_connect(24, 27, 60)


def check_travel(client, user, thread_id):
    current = location_names_reverse[user['Location']]
    if current == 0:
        reply = 'You cannot travel anywhere.'
    else:
        reply = ['You are in ' + location_names[current]]
        reply[0] += ' and can travel to the following places:'
        for i in adjacent_locations(user):
            reply.append('-> ' + location_names[i] + ': ' + str(edges[current][i]) + ' minutes away')
        if len(reply) > 1:
            reply = '\n'.join(reply)
        else:
            reply = 'You have not discovered any surrounding locations yet.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def travel_to_location(client, user, text, thread_id):
    current = location_names_reverse[user['Location']]
    location = _query_location(text, adjacent_locations(user))
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
        if time >= 0 and ((progress.get(location_names[i], 0) == 1) == discovered):
            locations.append(i)
    return locations


def _query_location(query, locations):
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