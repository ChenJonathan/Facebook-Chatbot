from fbchat.models import *
from datetime import datetime

from battle import begin_battle_quest, complete_battle_quest
from duel import begin_duel_quest
from location import location_features
from mongo import *
from util import *


def loop(client):
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
            if details['Status'] == ChatState.Delay:
                if now > details['EndTime']:
                    begin_battle_quest(client, user_from_id(user_id))
            elif details['Status'] == ChatState.Quest:
                if now > details['EndTime']:
                    complete_battle_quest(client, user_from_id(user_id), None)

        elif state == UserState.Duel:
            if details['Status'] == ChatState.Delay and now > details['EndTime']:
                    begin_duel_quest(client, user_from_id(user_id))