from fbchat.models import *
from datetime import datetime, timedelta
from threading import Lock
import math
import random

from data import monster_data
from mongo import *
from quest import generate_quest
from util import UserState, BattleState, level_to_stat_scale, total_atk, total_def, total_spd

quest_locks = {}


def generate_battle(client, user, thread_id):
    if user['Location'] not in monster_data:
        reply = 'There are no monsters in this location.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        return

    battle = {
        'Status': BattleState.Preparation,
        'Monster': random.choice(monster_data[user['Location']]).copy(),
        'ThreadID': thread_id
    }
    monster = battle['Monster']
    user_level = user['Stats']['Level']
    if user_level + 3 < monster['Level'][0]:
        monster_level = monster['Level'][0]
    elif user_level - 3 > monster['Level'][1]:
        monster_level = monster['Level'][1]
    else:
        lower_bound = max(user_level - 3, monster['Level'][0])
        upper_bound = min(user_level + 3, monster['Level'][1])
        monster_level = random.randint(lower_bound, upper_bound)
    stat_scale = level_to_stat_scale(monster_level) * (1 + (monster_level - 5) / 10)
    monster['Level'] = monster_level
    monster['ATK'] = int(monster['ATK'] * stat_scale)
    monster['DEF'] = int(monster['DEF'] * stat_scale)
    monster['SPD'] = int(monster['SPD'] * stat_scale)
    monster['HP'] = int(monster['HP'] * stat_scale * 3) // 10 * 10

    client.user_states[user['_id']] = (UserState.Battle, battle)
    reply = user['Name'] + ' has encountered a level ' + str(battle['Monster']['Level'])
    reply += ' ' + battle['Monster']['Name'] + '! Check your private messages (or message requests) '
    reply += 'to fight it.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = 'Use "!ready" to begin the fight. Use "!flee" at any point to cancel the fight.'
    client.send(Message(reply), thread_id=user['_id'])


def begin_battle(client, user):
    user_id = user['_id']
    state, details = client.user_states[user_id]

    details['Timer'] = _calculate_timer(total_spd(user), details['Monster']['SPD'])
    details['StartTime'] = datetime.now()
    details['EndTime'] = details['StartTime'] + timedelta(seconds=3)
    details['Status'] = BattleState.Delay

    quest_locks[user_id] = Lock()
    if user_id not in client.user_health:
        client.user_health[user_id] = user['Stats']['HP']

    reply = 'The battle has begun!'
    client.send(Message(reply), thread_id=user_id)
    reply = 'You will have ' + str(details['Timer']) + ' seconds to complete the next question.'
    client.send(Message(reply), thread_id=user_id)


def complete_battle(client, user, victory):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    monster = details['Monster']
    del client.user_states[user_id]

    quest_locks[user_id].release()
    del quest_locks[user_id]

    if victory:
        delta_experience = _calculate_experience(user['Stats']['Level'], monster['Level'])
        new_experience = user['Stats']['EXP'] + delta_experience
        delta_level = new_experience // 100
        delta_gold = _calculate_gold(user['Stats']['Level'], monster['Level'])
        experience_set(user_id, new_experience % 100)
        if delta_level:
            level_set(user_id, user['Stats']['Level'] + delta_level)
        gold_add(user['_id'], delta_gold)
        reply = 'You won the battle!'
        client.send(Message(reply), thread_id=user_id)
        reply = user['Name'] + ' has emerged victorious over the ' + monster['Name'] + ' and has received ' + \
                str(delta_experience) + ' experience and ' + str(delta_gold) + ' gold.'
        if delta_level:
            reply += ' ' + user['Name'] + ' has reached level ' + str(user['Stats']['Level'] + delta_level) + '!'
        client.send(Message(reply), thread_id=details['ThreadID'], thread_type=ThreadType.GROUP)
    else:
        reply = 'You have lost the battle.'
        client.send(Message(reply), thread_id=user_id)
        reply = user['Name'] + ' has been defeated by the ' + monster['Name'] + '.'
        client.send(Message(reply), thread_id=details['ThreadID'], thread_type=ThreadType.GROUP)


def cancel_battle(client, user):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    del client.user_states[user_id]
    flee_penalty = min(client.user_health[user_id], 10)
    client.user_health[user_id] -= flee_penalty
    reply = 'You have fled the battle, losing ' + str(flee_penalty) + ' health in the process. '
    if client.user_health[user_id] > 0:
        reply += 'You have ' + str(client.user_health[user_id]) + ' health remaining.'
    else:
        reply += 'You\'re now on the brink of death!'
    client.send(Message(reply), thread_id=user_id)
    reply = user['Name'] + ' has fled from the level ' + str(details['Monster']['Level']) + ' '
    reply += details['Monster']['Name'] + ', losing ' + str(flee_penalty) + ' health in the process.'
    client.send(Message(reply), thread_id=details['ThreadID'], thread_type=ThreadType.GROUP)


def begin_monster_quest(client, user):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    details['Quest'] = generate_quest('Vocab')
    details['StartTime'] = datetime.now()
    details['EndTime'] = details['StartTime'] + timedelta(seconds=details['Timer'])
    details['Status'] = BattleState.Quest
    reply = details['Quest']['Question']
    client.send(Message(reply), thread_id=user_id)


def complete_monster_quest(client, user, text):
    user_id = user['_id']
    if not (user_id in quest_locks and quest_locks[user_id].acquire(False)):
        return

    # Race condition safeguard
    state, details = client.user_states[user_id]
    if details['Status'] == BattleState.Delay:
        return

    # Calculate current hit
    monster = details['Monster']
    quest = details['Quest']
    if text == str(quest['Correct'] + 1):
        damage = _calculate_damage(total_atk(user), monster['DEF'])
        monster['HP'] = max(monster['HP'] - damage, 0)
        if details['Timer'] > 4:
            details['Timer'] -= 1
        reply = 'You dealt ' + str(damage) + ' damage to the enemy ' + monster['Name'] + '! It has '
        reply += str(monster['HP']) + ' health left.'
    else:
        damage = _calculate_damage(monster['ATK'], total_def(user))
        client.user_health[user_id] = max(client.user_health[user_id] - damage, 0)
        details['Timer'] = _calculate_timer(total_spd(user), monster['SPD'])
        reply = 'You\'ve been dealt ' + str(damage) + ' damage by the enemy ' + monster['Name'] + '. You have '
        reply += str(client.user_health[user_id]) + '/' + str(user['Stats']['HP']) + ' health left. '
        if text is None:
            reply += 'Be faster next time!'
        else:
            reply += 'The correct answer was "' + quest['Answers'][quest['Correct']] + '".'

    # User loses
    if monster['HP'] <= 0:
        client.send(Message(reply), thread_id=user_id)
        complete_battle(client, user, True)
        return

    # User wins
    elif client.user_health[user_id] <= 0:
        client.send(Message(reply), thread_id=user_id)
        complete_battle(client, user, False)
        return

    # Battle ongoing
    else:
        details['StartTime'] = datetime.now()
        details['EndTime'] = details['StartTime'] + timedelta(seconds=3)
        details['Status'] = BattleState.Delay
        reply += '\n\nYou will have ' + str(details['Timer']) + ' seconds to complete the next question.'
        client.send(Message(reply), thread_id=user_id)

    quest_locks[user_id].release()


def _calculate_damage(attack, defence):
    damage = random.uniform(attack * 0.8, attack * 1.2) - random.uniform(defence * 0.4, defence * 0.6)
    return max(int(damage), 1)


def _calculate_timer(user_speed, monster_speed):
    return 4 + int(math.sqrt(max(user_speed * 2 - monster_speed, 0)) * 2)


def _calculate_experience(user_level, monster_level):
    experience = math.sqrt(monster_level / user_level) * 5
    experience *= random.uniform(0.8, 1.2)
    experience /= max((user_level - monster_level) / 2, 1)
    return max(int(experience), 0)


def _calculate_gold(user_level, monster_level):
    gold = (math.sqrt(monster_level + 64) - 7) * 400
    gold *= random.uniform(0.8, 1.2)
    gold /= max((user_level - monster_level) / 2, 1)
    return max(int(gold), 0)