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
_connect(6, 7, 1)
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
_connect(15, 16, 1)
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
_connect(25, 26, 1)
#_connect(24, 27, 60)


def check_travel(client, user, thread_id):
    current = location_names_reverse[user['Location']]
    if current == 0:
        reply = 'You cannot travel anywhere.'
    else:
        progress = user['LocationProgress']
        reply = ['You are in ' + location_names[current]]
        reply[0] += ' and can travel to the following places:'
        for i, time in enumerate(edges[current]):
            if time >= 0 and progress.get(location_names[i], 0) == 1:
                reply.append('-> ' + location_names[i] + ': ' + str(time) + ' minutes away')
        if len(reply) > 1:
            reply = '\n'.join(reply)
        else:
            reply = 'You have not discovered any surrounding locations yet.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def travel_to_location(client, user, text, thread_id):
    current = location_names_reverse[user['Location']]
    progress = user['LocationProgress']
    location = query_location(text)
    if location is None:
        reply = 'That location doesn\'t exist.'
    elif edges[current][location] < 0 or progress.get(location_names[location], 0) < 1:
        reply = 'You cannot travel there.'
    else:
        user_id = user['_id']
        lock_acquire(user_id)
        try:
            client.user_states[user_id] = (UserState.Travel, {
                'Destination': location_names[location],
                'EndTime': datetime.now() + timedelta(minutes=edges[current][location])
            })
        finally:
            lock_release(user_id)
        reply = user['Name'] + ' is now traveling to ' + location_names[location] + '.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)