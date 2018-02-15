from fbchat.models import *
from datetime import datetime
import time
import traceback

from battle import begin_monster_quest, complete_monster_quest
from location import location_features
from mongo import *
from util import *


def loop(client):
    try:

        time.sleep(0.1)
        now = datetime.now()
        for user_id, record in list(client.user_states.items()):
            state, details = record
            lock_acquire(user_id)
            try:

                if state == UserState.Travel:
                    if now > details['EndTime']:
                        location_set(user_id, details['Destination'])
                        del client.user_states[user_id]
                        user = user_from_id(user_id)
                        features = location_features(user['Location'])
                        reply = 'You have reached ' + user['Location'] + '! '
                        if features:
                            reply += 'The following services are available here:'
                            for feature in features:
                                reply += '\n-> ' + feature
                        else:
                            reply += 'There are no services available here.'
                        client.send(Message(reply), thread_id=user_id)

                elif state == UserState.Battle:
                    if details['Status'] == BattleState.Delay:
                        if now > details['EndTime']:
                            begin_monster_quest(client, user_from_id(user_id))
                    elif details['Status'] == BattleState.Quest:
                        if now > details['EndTime']:
                            complete_monster_quest(client, user_from_id(user_id), None)

            finally:
                lock_release(user_id)

    except:
        client.send(Message('Polling: ' + traceback.format_exc()), thread_id=master_id)