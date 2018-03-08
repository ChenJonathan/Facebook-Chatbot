from fbchat.models import *
from datetime import datetime, timedelta
import random

from data import monster_data
from enums import UserState, ChatState
from mongo import *
from quest import generate_quest
from util import *


def generate_battle(client, user, thread_id):
    if user['Location'] not in monster_data:
        reply = 'There are no monsters in this location.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        return

    battle = {
        'Status': ChatState.PREPARING,
        'Monster': random.choice(monster_data[user['Location']]).copy(),
        'ThreadID': thread_id
    }
    monster = battle['Monster']
    if 'Level' in monster:
        monster['Level'] = random.randint(monster['Level'][0], monster['Level'][1])
    else:
        monster['Level'] = random.randint(int(user['Stats']['Level'] * 0.9), int(user['Stats']['Level'] * 1.1))
    stat_scale = base_stat(monster['Level']) * 2.25
    monster['ATK'] = int(monster['ATK'] * stat_scale)
    monster['DEF'] = int(monster['DEF'] * stat_scale)
    monster['SPD'] = int(monster['SPD'] * stat_scale)
    monster['Health'] = int(monster['Health'] * (stat_scale ** 2) / 20) // 10 * 10

    client.user_states[user['_id']] = (UserState.BATTLE, battle)
    reply = user['Name'] + ' has encountered a level ' + str(battle['Monster']['Level']) + ' '
    reply += battle['Monster']['Name'] + '! Check your private messages (or message requests) to fight it.'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    reply = 'You are facing a level ' + str(battle['Monster']['Level']) + ' '
    reply += battle['Monster']['Name'] + '! Use "!ready" to begin the battle. '
    reply += 'Use "!flee" at any point to cancel the battle (at the cost of 10 health).'
    client.send(Message(reply), thread_id=user['_id'])


def begin_battle(client, user):
    user_id = user['_id']
    state, details = client.user_states[user_id]

    details['Status'] = ChatState.DELAY
    details['Timer'] = _calculate_timer(total_spd(user), details['Monster']['SPD'])
    details['StartTime'] = datetime.now()
    details['EndTime'] = details['StartTime'] + timedelta(seconds=3)

    reply = 'The battle has begun!'
    client.send(Message(reply), thread_id=user_id)
    reply = 'You will have ' + str(details['Timer']) + ' seconds to complete the next question.'
    client.send(Message(reply), thread_id=user_id)


def complete_battle(client, user, victory):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    monster = details['Monster']

    del client.user_states[user_id]

    if victory:
        delta_experience = _calculate_experience(user['Stats']['Level'], monster['Level'])
        new_experience = user['Stats']['Experience'] + delta_experience
        delta_level = new_experience // 100
        delta_gold = _calculate_gold(user['Stats']['Level'], monster['Level'], user['GoldFlow'])
        experience_set(user_id, new_experience % 100)
        if delta_level:
            level_set(user_id, user['Stats']['Level'] + delta_level)
        gold_add(user_id, delta_gold)
        reply = 'You won the battle!'
        client.send(Message(reply), thread_id=user_id)
        reply = user['Name'] + ' has emerged victorious over the ' + monster['Name'] + ' and has received '
        reply += str(delta_experience) + ' experience and ' + format_num(delta_gold, truncate=True) + ' gold.'
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

    if user_id not in client.user_health:
        client.user_health[user_id] = user['Stats']['Health']
    flee_penalty = min(client.user_health[user_id], 10)
    client.user_health[user_id] -= flee_penalty

    reply = 'You have fled the battle, losing ' + str(flee_penalty) + ' health in the process. '
    if client.user_health[user_id] > 0:
        reply += 'You have ' + str(client.user_health[user_id]) + ' health remaining.'
    else:
        reply += 'You\'re now on the brink of death!'
    client.send(Message(reply), thread_id=user_id)
    reply = user['Name'] + ' has fled from the level ' + str(details['Monster']['Level'])
    reply += ' ' + details['Monster']['Name']
    reply += '.' if client.user_health[user_id] > 0 else ' and is now on the brink of death!'
    client.send(Message(reply), thread_id=details['ThreadID'], thread_type=ThreadType.GROUP)


def begin_battle_quest(client, user):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    details['Status'] = ChatState.QUEST
    details['Quest'] = generate_quest('Vocab')
    details['StartTime'] = datetime.now()
    details['EndTime'] = details['StartTime'] + timedelta(seconds=details['Timer'])
    client.send(Message(details['Quest']['Question']), thread_id=user_id)


def complete_battle_quest(client, user, text):
    user_id = user['_id']
    state, details = client.user_states[user_id]
    if user_id not in client.user_health:
        client.user_health[user_id] = user['Stats']['Health']

    # Calculate user damage
    monster = details['Monster']
    quest = details['Quest']
    if text == str(quest['Correct'] + 1):
        damage = _calculate_damage(total_atk(user), monster['DEF'], scale=base_stat(user['Stats']['Level']) / 10)
        monster['Health'] = max(monster['Health'] - damage, 0)
        if details['Timer'] > 1:
            details['Timer'] -= 1

        if damage == 1:
            reply = 'Your attack was too weak and dealt only 1 damage to the enemy ' + monster['Name']
            reply += '. It has ' + str(monster['Health']) + ' health left.'
        else:
            reply = 'You dealt ' + str(damage) + ' damage to the enemy ' + monster['Name'] + '! It has '
            reply += str(monster['Health']) + ' health left.'

        # User wins
        if monster['Health'] <= 0:
            client.send(Message(reply), thread_id=user_id)
            complete_battle(client, user, True)
            return

    # Calculate opponent damage
    else:
        damage = _calculate_damage(monster['ATK'], total_def(user))
        damage = max(damage, 1)
        client.user_health[user_id] = max(client.user_health[user_id] - damage, 0)
        details['Timer'] = _calculate_timer(total_spd(user), monster['SPD'])

        reply = 'You\'ve been dealt ' + str(damage) + ' damage by the enemy ' + monster['Name'] + '. You have '
        reply += str(client.user_health[user_id]) + '/' + str(user['Stats']['Health']) + ' health left. '
        if text is None:
            reply += 'Be faster next time!'
        else:
            reply += 'The correct answer was "' + quest['Answers'][quest['Correct']] + '".'

        # User loses
        if client.user_health[user_id] <= 0:
            client.send(Message(reply), thread_id=user_id)
            complete_battle(client, user, False)
            return

    # Battle ongoing
    details['StartTime'] = datetime.now()
    details['EndTime'] = details['StartTime'] + timedelta(seconds=3)
    details['Status'] = ChatState.DELAY
    reply += '\n\nYou will have ' + str(details['Timer']) + ' second'
    reply += ('' if details['Timer'] == 1 else 's') + ' to complete the next question.'
    client.send(Message(reply), thread_id=user_id)


def _calculate_damage(user_attack, opponent_defence, scale=1):
    damage = (user_attack - opponent_defence)
    if damage >= 0:
        damage = (damage / 15 + 2) * 5
    else:
        damage = math.sqrt(max(damage / 10 + 4, 0)) * 5
    return max(int(damage * scale * random.uniform(0.8, 1.2)), 1)


def _calculate_timer(user_speed, monster_speed):
    timer = user_speed - monster_speed
    if timer >= 0:
        timer = int(math.sqrt(timer + 9) * 2)
    else:
        timer = int(math.sqrt(max(timer + 36, 0)))
    return 3 + int(timer)


def _calculate_experience(user_level, monster_level):
    experience = monster_level - user_level + 10
    return max(int(experience * random.uniform(0.8, 1.2)), 0)


def _calculate_gold(user_level, monster_level, user_gold_flow):
    percent = max(monster_level - user_level + 10, 0) * random.uniform(2, 3)
    return int(percent * (user_gold_flow / 100 + 10))