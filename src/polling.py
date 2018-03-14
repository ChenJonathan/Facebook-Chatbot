from fbchat.models import *
from datetime import datetime

from battle import begin_battle_quest, complete_battle_quest
from duel import begin_duel_quest
from enums import UserState, ChatState
from location import location_features, location_level
from mongo import *


def loop(client):
    now = datetime.now()
    for user_id, record in list(client.user_states.items()):
        state, details = record

        if state == UserState.TRAVEL:
            if now > details['EndTime']:
                location_set(user_id, details['Destination'])
                del client.user_states[user_id]
                user = user_from_id(user_id)
                features = location_features(user['Location'])
                level_range = location_level(user['Location'])
                reply = 'You have reached ' + user['Location'] + '!'
                if level_range:
                    if level_range == (None, None):
                        reply += ' The monsters here scale to your level. '
                    else:
                        reply += ' The monsters here are levels ' + str(level_range[0])
                        reply += ' to ' + str(level_range[1]) + '. '
                if features:
                    reply += ' The following services are available here:'
                    for feature in features:
                        reply += '\n-> ' + feature
                client.send(Message(reply), thread_id=user_id)

        elif state == UserState.BATTLE:
            if details['Status'] == ChatState.DELAY:
                if now > details['EndTime']:
                    begin_battle_quest(client, user_from_id(user_id))
            elif details['Status'] == ChatState.QUEST:
                if now > details['EndTime']:
                    complete_battle_quest(client, user_from_id(user_id), None)

        elif state == UserState.DUEL:
            if details['Status'] == ChatState.DELAY and now > details['EndTime']:
                    begin_duel_quest(client, user_from_id(user_id))