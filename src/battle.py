from fbchat.models import *
from datetime import datetime, timedelta
from threading import Lock

from mongo import *
from quest import generate_quest
from util import UserState, BattleState

quest_lock = Lock()


def generate_battle(client, user, thread_id):
    battle = {
        'Status': BattleState.Preparation,
        'Monster': {
            'Name': 'Orange Mushroom',
            'Level': 1,
            'ATK': 10,
            'DEF': 10,
            'SPD': 10,
            'HP': 50
        },
        'ThreadID': thread_id
    }
    client.user_states[user['_id']] = (UserState.Battle, battle)
    reply = user['Name'] + ' has encountered a level ' + str(battle['Monster']['Level'])
    reply += ' ' + battle['Monster']['Name'] + '!'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = 'Use "!ready" to begin the fight and !flee to cancel it.'
    client.send(Message(reply), thread_id=user['_id'])


def begin_battle(client, user):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    details['Quest'] = generate_quest('Vocab')
    details['Timer'] = 10
    details['EndTime'] = datetime.now() + timedelta(seconds=details['Timer'])
    details['Status'] = BattleState.Battle
    if user_id not in client.user_health:
        client.user_health[user_id] = user['Stats']['HP']
    reply = 'The battle has begun!'
    client.send(Message(reply), thread_id=user_id)
    reply = details['Quest']['Question'] + '\n(You have ' + str(details['Timer']) + ' seconds)'
    client.send(Message(reply), thread_id=user_id)


def cancel_battle(client, user):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    del client.user_states[user_id]
    reply = 'You have fled the battle.'
    client.send(Message(reply), thread_id=user_id)
    reply = user['Name'] + ' has fled from the level ' + str(details['Monster']['Level'])
    reply += ' ' + details['Monster']['Name'] + '.'
    client.send(Message(reply), thread_id=details['ThreadID'], thread_type=ThreadType.GROUP)


def complete_monster_quest(client, user, text):
    if not quest_lock.acquire(False):
        return

    user_id = user['_id']
    state, details = client.user_states[user_id]
    monster = details['Monster']
    quest = details['Quest']
    if text is not None and text == str(quest['Correct'] + 1):
        monster['HP'] -= 10
        if details['Timer'] > 4:
            details['Timer'] -= 1
        reply = 'You have dealt ' + str(10) + ' damage to the enemy ' + monster['Name'] + '!'
    else:
        client.user_health[user_id] -= 10
        details['Timer'] = 10
        reply = 'You have been dealt ' + str(10) + ' damage by the enemy ' + monster['Name'] + '. '
        reply += 'The correct answer was "' + quest['Answers'][quest['Correct']] + '".'
    client.send(Message(reply), thread_id=user_id)

    if monster['HP'] <= 0:
        del client.user_states[user_id]
        del client.user_health[user_id]
        reply = 'You win!'
        client.send(Message(reply), thread_id=user_id)
        reply = user['Name'] + ' has emerged victorious over the ' + monster['Name'] + '!'
        client.send(Message(reply), thread_id=details['ThreadID'], thread_type=ThreadType.GROUP)
        return

    elif client.user_health[user_id] <= 0:
        del client.user_states[user_id]
        del client.user_health[user_id]
        reply = 'You lose.'
        client.send(Message(reply), thread_id=user_id)
        reply = user['Name'] + ' has lost in battle to the ' + monster['Name'] + '.'
        client.send(Message(reply), thread_id=details['ThreadID'], thread_type=ThreadType.GROUP)
        return

    details['Quest'] = generate_quest('Vocab')
    details['EndTime'] = datetime.now() + timedelta(seconds=details['Timer'])
    reply = details['Quest']['Question'] + '\n(You have ' + str(details['Timer']) + ' seconds)'
    client.send(Message(reply), thread_id=user_id)

    quest_lock.release()