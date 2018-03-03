from fbchat.models import *
from datetime import datetime, timedelta
import random

from mongo import *
from quest import generate_quest
from util import *


def send_duel_request(client, user, opponent, gold, thread_id):
    user_id = user['_id']
    opponent_id = opponent['_id']
    opponent_target, opponent_amount = client.duel_requests.get(opponent_id, (None, None))
    if user_id in client.duel_requests:
        gold_add(user_id, client.duel_requests[user_id][1] - gold)
        del client.duel_requests[user_id]
    else:
        gold_add(user_id, -gold)
    if opponent_target != user_id or gold != opponent_amount:
        client.duel_requests[user_id] = (opponent_id, gold)
        reply = user['Name'] + ' challenges ' + opponent['Name'] + ' to a duel for ' + str(gold)
        reply += ' gold! Use "!duel <amount> <name>" on the person who challenged you with the '
        reply += 'same <amount> to accept the challenge.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    else:
        del client.duel_requests[opponent_id]
        generate_duel(client, opponent, user, gold, thread_id)


def cancel_duel_request(client, user, thread_id):
    user_id = user['_id']
    if user_id in client.duel_requests:
        gold_add(user_id, client.duel_requests[user_id][1])
        del client.duel_requests[user_id]
        reply = 'Your duel request has been cancelled.'
    else:
        reply = 'You do not have an active duel request.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)


def generate_duel(client, user_1, user_2, gold, thread_id):
    duel_1 = {
        'Status': ChatState.Preparing,
        'Gold': gold,
        'UserHealth': user_1['Stats']['Health'],
        'OpponentHealth': user_2['Stats']['Health'],
        'OpponentID': user_2['_id'],
        'ThreadID': thread_id
    }
    duel_2 = duel_1.copy()
    duel_2['UserHealth'] = user_2['Stats']['Health']
    duel_2['OpponentHealth'] = user_1['Stats']['Health']
    duel_2['OpponentID'] = user_1['_id']

    client.user_states[user_1['_id']] = (UserState.Duel, duel_1)
    client.user_states[user_2['_id']] = (UserState.Duel, duel_2)
    reply = user_2['Name'] + ' has accepted a duel with ' + user_1['Name'] + ' for ' + str(gold)
    reply += ' gold! Check your private messages (or message requests) to begin the duel.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = 'You are in a duel with ' + user_2['Name'] + '! Use "!ready" to begin the duel. '
    reply += 'Use "!flee" at any point to forfeit the duel. Forfeiting after the duel begins will '
    reply += 'result in a loss. You will receive a new question after the current one is answered.'
    client.send(Message(reply), thread_id=user_1['_id'])
    reply = 'You are in a duel with ' + user_1['Name'] + '! Use "!ready" to begin the duel. '
    reply += 'Use "!flee" at any point to forfeit the duel. Forfeiting after the duel begins will '
    reply += 'result in a loss. You will receive a new question after the current one is answered.'
    client.send(Message(reply), thread_id=user_2['_id'])


def begin_duel(client, user):
    user_id = user['_id']
    user_state, user_details = client.user_states[user_id]
    opponent_id = user_details['OpponentID']
    opponent = user_from_id(opponent_id)
    opponent_state, opponent_details = client.user_states[opponent_id]

    if opponent_details['Status'] == ChatState.Ready:
        user_details['Status'] = ChatState.Delay
        user_details['StartTime'] = datetime.now()
        user_details['EndTime'] = user_details['StartTime'] + timedelta(seconds=3)
        opponent_details['Status'] = ChatState.Delay
        opponent_details['StartTime'] = user_details['StartTime']
        opponent_details['EndTime'] = user_details['EndTime']

        reply = 'The duel has begun!'
        client.send(Message(reply), thread_id=user_id)
        reply = user['Name'] + ' is ready. ' + reply
        client.send(Message(reply), thread_id=opponent_id)
    else:
        user_details['Status'] = ChatState.Ready

        reply = 'Now waiting for ' + opponent['Name'] + ' to be ready.'
        client.send(Message(reply), thread_id=user_id)
        reply = user['Name'] + ' is ready to begin the duel.'
        client.send(Message(reply), thread_id=opponent_id)


def complete_duel(client, winner, loser):
    winner_id = winner['_id']
    winner_state, winner_details = client.user_states[winner_id]
    loser_id = loser['_id']

    del client.user_states[winner_id]
    del client.user_states[loser_id]

    gold = winner_details['Gold']
    gold_add(winner_id, gold * 2)

    reply = 'You won the duel!'
    client.send(Message(reply), thread_id=winner_id)
    reply = 'You have lost the duel.'
    client.send(Message(reply), thread_id=loser_id)
    reply = winner['Name'] + ' has defeated ' + loser['Name'] + ' in a duel with '
    reply += str(winner_details['UserHealth']) + '/' + str(winner['Stats']['Health']) + ' health remaining! '
    reply += winner['Name'] + ' receives ' + str(gold) + ' gold from ' + loser['Name'] + '.'
    client.send(Message(reply), thread_id=winner_details['ThreadID'], thread_type=ThreadType.GROUP)


def cancel_duel(client, user):
    user_id = user['_id']
    user_state, user_details = client.user_states[user_id]
    opponent_id = user_details['OpponentID']
    opponent = user_from_id(opponent_id)

    del client.user_states[user_id]
    del client.user_states[opponent_id]

    gold = user_details['Gold']

    if user_details['Status'] == ChatState.Preparing or user_details['Status'] == ChatState.Ready:
        gold_add(user_id, gold)
        gold_add(opponent_id, gold)

        reply = 'The duel was cancelled prematurely. All gold will be refunded.'
        client.send(Message(reply), thread_id=user_id)
        reply = 'The duel has been cancelled by ' + user['Name'] + ' prematurely. All gold will be refunded.'
        client.send(Message(reply), thread_id=opponent_id)
        reply = 'The duel between ' + opponent['Name'] + ' and ' + user['Name']
        reply += ' has been cancelled prematurely. All gold will be refunded.'
    else:
        gold_add(opponent_id, gold * 2)

        reply = 'You have forfeited the duel.'
        client.send(Message(reply), thread_id=user_id)
        reply = user['Name'] + ' forfeits. You won the duel!'
        client.send(Message(reply), thread_id=opponent_id)
        reply = user['Name'] + ' forfeits the duel! ' + opponent['Name']
        reply += ' receives ' + str(gold) + ' gold from ' + user['Name'] + '.'
        client.send(Message(reply), thread_id=user_details['ThreadID'], thread_type=ThreadType.GROUP)


def begin_duel_quest(client, user):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    details['Status'] = ChatState.Quest
    details['Quest'] = generate_quest('Vocab')
    client.send(Message(details['Quest']['Question']), thread_id=user_id)


def complete_duel_quest(client, user, text):
    user_id = user['_id']
    user_state, user_details = client.user_states[user_id]
    opponent_id = user_details['OpponentID']
    opponent = user_from_id(opponent_id)
    opponent_state, opponent_details = client.user_states[opponent_id]
    if user_id not in client.user_health:
        client.user_health[user_id] = user['Stats']['Health']
    if opponent_id not in client.user_health:
        client.user_health[opponent_id] = opponent['Stats']['Health']

    # Calculate user damage
    quest = user_details['Quest']
    if text == str(quest['Correct'] + 1):
        damage = _calculate_damage(total_atk(user), total_def(opponent))
        opponent_health = max(user_details['OpponentHealth'] - damage, 0)
        user_details['OpponentHealth'] = opponent_health
        opponent_details['UserHealth'] = opponent_health

        reply = user['Name'] + ' dealt ' + str(damage) + ' damage to you! '
        reply += 'You have ' + str(opponent_health) + ' health left.'
        client.send(Message(reply), thread_id=opponent_id)
        reply = 'You dealt ' + str(damage) + ' damage to ' + opponent['Name'] + '! '
        reply += opponent['Name'] + ' has ' + str(opponent_health) + ' health left. '

    # User fumbles
    else:
        reply = 'You fumbled your attack! ' + opponent['Name'] + ' has ' + str(user_details['OpponentHealth'])
        reply += ' health left. The correct answer was "' + quest['Answers'][quest['Correct']] + '".'

    # User wins
    if user_details['OpponentHealth'] <= 0:
        client.send(Message(reply), thread_id=user_id)
        complete_duel(client, user, opponent)
        return

    # Battle ongoing
    user_details['Status'] = ChatState.Delay
    user_details['Timer'] = _calculate_timer(total_spd(user), total_spd(opponent))
    user_details['StartTime'] = datetime.now()
    user_details['EndTime'] = user_details['StartTime'] + timedelta(seconds=user_details['Timer'])
    reply += '\n\nYour next question will arrive in ' + str(user_details['Timer']) + ' seconds.'
    client.send(Message(reply), thread_id=user_id)


def _calculate_damage(user_attack, opponent_defence):
    damage = (user_attack - opponent_defence)
    if damage >= 0:
        damage = (damage / 15 + 2) * 5
    else:
        damage = math.sqrt(max(damage / 10 + 4, 0)) * 5
    return max(int(damage * random.uniform(0.8, 1.2)), 1)


def _calculate_timer(user_speed, opponent_speed):
    return int(math.sqrt(max(opponent_speed - user_speed, 0) * 4 / 3 + 9))