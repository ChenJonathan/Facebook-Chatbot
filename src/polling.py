from fbchat.models import *
from datetime import datetime
import traceback

from battle import begin_monster_quest, complete_monster_quest
from location import location_features
from mongo import *
from util import UserState, BattleState, master_id


def loop(client):
    try:

        now = datetime.now()
        for user_id, record in list(client.user_states.items()):
            state, details = record

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

    except:
        client.send(Message(traceback.format_exc()), thread_id=master_id)