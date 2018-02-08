from fbchat.models import *
from datetime import datetime, timedelta
import math
import random
import requests

from craft import generate_craft_info, craft_item
from emoji import random_emoji
from hearthstone import random_beast
from info import generate_user_info, generate_group_info
from location import location_features, explore_location
from mongo import *
from quest import set_quest_type, generate_quest
from shop import generate_shop_info, shop_purchase
from travel import check_travel, travel_to_location
from util import *

def check_busy(client, user, thread_id):
    if user['_id'] not in client.travel_record:
        return False

    # Check if traveling has expired
    record = client.travel_record[user['_id']]
    now = datetime.now()
    if now > record[1]:
        location_set(user['_id'], record[0])
        del client.travel_record[user['_id']]
        return False

    # Check travel time remaining
    minutes = math.ceil((record[1] - datetime.now()).total_seconds() / 60)
    reply = 'You\'re busy traveling to ' + location_names[record[0]]
    reply += '. (' + str(minutes) + ' minute' + ('' if minutes == 1 else 's')
    reply += ' remaining).'
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    return True

def run_user_command(client, author, command, text):
    author_id = author['_id']
    if author_id != master_id:
        return

    if command == 'alias' or command == 'a':
        alias, user, *_ = text.split(' ', 1) + ['']
        alias = alias.lower()
        if len(user) > 0:
            user = client.searchForUsers(user)[0]
            alias_add(user.uid, alias)
            message = Message(user.name + '\'s alias has been set to ' + alias + '.')
        else:
            user = user_from_alias(alias)
            if user:
                alias_remove(alias)
                message = Message(user['name'] + '\'s alias has been unset.')
            else:
                message = Message('Alias not found.')
        client.send(message, thread_id=author_id)

    elif command == 'check' or command == 'c':
        if len(text) > 0:
            users = [user_from_alias(text.lower())]
            if not users[0]:
                client.send(Message('Alias not found.'), thread_id=author_id)
                return
        else:
            users = alias_get_all()
        reply = []
        for user in users:
            line = '<<' + user['name'] + '>> (' + user['alias'] + ')\n'
            line += 'Priority: ' + priority_names[user['priority']] + '\n'
            line += 'Score: ' + str(calculate_score(user)) + '\n'
            line += 'Gold: ' + str(user['gold']) + ' (+' + str(user['gold_rate']) + '/hour)\n'
            line += 'Location: ' + location_names[user['location']]
            if user['_id'] in client.travel_record:
                record = client.travel_record[user['_id']]
                minutes = math.ceil((record[1] - datetime.now()).total_seconds() / 60)
                line += ' -> ' + location_names[record[0]] + '\n'
                line += '(' + str(minutes) + ' minute' + ('' if minutes == 1 else 's')
                line += ' remaining)'
            reply.append(line)
        reply = '\n\n'.join(reply) if reply else 'No aliases set.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'define' or command == 'd':
        command, text, *_ = text.split(' ', 1) + ['']
        command = command.lower()
        text = text.strip()
        if len(text) > 0:
            client.defines[command] = text
        elif len(command) > 0:
            del client.defines[command]

    elif command == 'help' or command == 'h':
        generate_user_info(client, text, author)

    elif command == 'message' or command == 'm':
        alias, reply, *_ = text.split(' ', 1) + ['']
        user = user_from_alias(alias.lower())
        if not user:
            client.send(Message('Alias not found.'), thread_id=author_id)
        elif len(reply) > 0:
            client.send(Message(reply), thread_id=user['_id'])
        else:
            client.send(Message(emoji_size=EmojiSize.SMALL), thread_id=user['_id'])

    elif command == 'perm' or command == 'p':
        priority, alias = text.split(' ', 1)
        priority = int(priority)
        user = user_from_alias(alias.lower())
        if not user:
            message = Message('Alias not found.')
        elif user['_id'] == master_id:
            message = Message('Cannot modify master priority.')
        elif priority < 0 or priority >= master_priority:
            message = Message('Invalid priority.')
        else:
            priority_set(user['_id'], priority)
            reply = user['name'] + '\'s priority has been set to ' + str(priority)
            reply += ' (' + priority_names[priority] + ').'
            message = Message(reply)
        client.send(message, thread_id=author_id)

    elif command == 'secret' or command == 's':
        reply = []
        if client.defines:
            section = '<<Defines>>\n'
            section += '\n'.join(['"' + i + '": ' + j for i, j in client.defines.items()])
            reply.append(section)
        if client.responses:
            section = '<<Responses>>\n'
            section += '\n'.join(['"' + response + '"' for response in client.responses])
            reply.append(section)
        reply = '\n\n'.join(reply) if reply else 'No secrets active.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'wong' or command == 'w':
        if len(text) > 0:
            client.responses.append(text)
        elif len(text) == 1:
            client.responses.clear()

def run_group_command(client, author, command, text, thread_id):
    author_id = author['_id']

    if command == 'alias' or command == 'a':
        if author_id == master_id:
            alias, user, *_ = text.split(' ', 1) + ['']
            alias = alias.lower()
            if len(user) > 0:
                user = client.matchUser(thread_id, user)
                if user:
                    alias_add(user.uid, alias)
                    reply = user.name + '\'s alias has been set to ' + alias + '.'
                else:
                    reply = 'User not found.'
            else:
                user = user_from_alias(alias)
                if user:
                    alias_remove(alias)
                    reply = user['name'] + '\'s alias has been unset.'
                else:
                    reply = 'Alias not found.'
        else:
            reply = 'You don\'t have permission to do this.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'booli':
        message = Message('Deprecated - please use !bully instead.')
        client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'bully' or command == 'b':
        if len(text) == 0:
            user = client.fetchUserInfo(author_id)[author_id]
        else:
            user = client.matchUser(thread_id, text)
        if user:
            if exceeds_priority(user.uid, author_id):
                reply = user.name + ' is a cool guy.'
                client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
                user = client.fetchUserInfo(author_id)[author_id]
            url = 'https://insult.mattbas.org/api/insult.txt?who=' + user.name
            reply = requests.get(url).text + '.'
        else:
            reply = 'User not found.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'check' or command == 'c':
        if len(text) > 0:
            user = client.matchUser(thread_id, text)
            if not user:
                message = Message('User not found.')
                client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                return
            user = user_from_id(user.uid)
        else:
            user = user_from_id(author_id)
        reply = '<<' + user['name'] + '>>\n'
        reply += 'Priority: ' + priority_names[user['priority']] + '\n'
        reply += 'Score: ' + str(calculate_score(user)) + '\n'
        reply += 'Gold: ' + str(user['gold']) + ' (+' + str(user['gold_rate']) + '/hour)\n'
        reply += 'Location: ' + location_names[user['location']]
        if user['_id'] in client.travel_record:
            record = client.travel_record[user['_id']]
            minutes = math.ceil((record[1] - datetime.now()).total_seconds() / 60)
            reply += ' -> ' + location_names[record[0]] + '\n'
            reply += '(' + str(minutes) + ' minute' + ('' if minutes == 1 else 's')
            reply += ' remaining)'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'craft':
        if check_busy(client, author, thread_id):
            return
        elif 'Crafting' not in location_features(author['location']):
            message = Message('There is no crafting station in this location.')
            client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif len(text) == 0:
            generate_craft_info(client, author, thread_id)
        else:
            craft_item(client, author, text, thread_id)

    elif command == 'daily' or command == 'd':
        text = text.strip().lower()
        if text not in ['color', 'emoji']:
            return
        subscriptions = subscription_get(thread_id)
        if text in subscriptions:
            subscription_remove(thread_id, text)
            reply = 'This conversation has been unsubscribed from daily ' + text + 's.'
        else:
            subscription_add(thread_id, text)
            reply = 'This conversation has been subscribed to daily ' + text + 's.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'equip':
        weapon = author['equipment']['Weapon']
        armor = author['equipment']['Armor']
        reply = '<<Equipment>>\n'
        reply += 'Weapon: ' + weapon['Name'] + '\n'
        reply += '-> ATK: ' + str(weapon['ATK']) + '\n'
        reply += '-> DEF: ' + str(weapon['DEF']) + '\n'
        reply += '-> SPD: ' + str(weapon['SPD']) + '\n'
        reply += 'Armor: ' + armor['Name'] + '\n'
        reply += '-> ATK: ' + str(armor['ATK']) + '\n'
        reply += '-> DEF: ' + str(armor['DEF']) + '\n'
        reply += '-> SPD: ' + str(armor['SPD'])
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'explore' or command == 'e':
        if author_id in client.explore_record:
            reply = 'You can only explore once per hour.'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif not check_busy(client, author, thread_id):
            client.explore_record.add(author_id)
            explore_location(client, author, thread_id)

    elif command == 'give' or command == 'g':
        amount, user = text.split(' ', 1)
        amount = int(amount)
        if amount < 1 and author_id != master_id:
            reply = 'Invalid amount of gold.'
        else:
            user = client.matchUser(thread_id, user)
            gold = gold_get(author_id)
            if gold < amount:
                reply = 'Not enough gold.'
            elif author_id == user.uid:
                reply = 'Cannot give gold to self.'
            else:
                gold_add(author_id, -amount)
                gold_add(user.uid, amount)
                reply = author['name'] + ' gives ' + str(amount)
                reply += ' gold to ' + user.name + '.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'help' or command == 'h':
        generate_group_info(client, text, author, thread_id)

    elif command == 'inventory' or command == 'i':
        reply = 'Your inventory has been sent to you in private chat.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
        reply = ['<<Inventory>>']
        for item, amount in author['inventory'].items():
            reply.append(item + ' x ' + str(amount))
        reply = '\n'.join(reply) if len(reply) > 1 else 'Your inventory is empty.'
        client.send(Message(reply), thread_id=author_id, thread_type=ThreadType.USER)

    elif command == 'jail' or command == 'j':
        if author['priority'] >= master_priority - 1:
            if len(text) == 0:
                reply = 'Please specify a user.'
            else:
                user = client.matchUser(thread_id, text)
                if not user:
                    message = Message('User not found.')
                    client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                    return
                user = user_from_id(user.uid)
                if user['_id'] == master_id and author_id != master_id:
                    user = author
                if user['location'] == 0:
                    location_set(user['_id'], 1)
                    if user['_id'] in client.travel_record:
                        del client.travel_record[user['_id']]
                    reply = user['name'] + ' has been freed from jail.'
                else:
                    location_set(user['_id'], 0)
                    if user['_id'] in client.travel_record:
                        del client.travel_record[user['_id']]
                    reply = user['name'] + ' has been sent to jail!'
        else:
            reply = 'You don\'t have permission to do this.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'location' or command == 'l':
        features = location_features(author['location'])
        reply = 'Welcome to ' + location_names[author['location']] + '!'
        if features:
            reply += ' The following services are available here:\n'
            for feature in features:
                reply += '-> ' + feature
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'mute' or command == 'm':
        if len(text) == 0:
            client.removeUserFromGroup(author_id, thread_id)
            return
        user = client.matchUser(thread_id, text)
        if user:
            if exceeds_priority(user.uid, author_id):
                client.removeUserFromGroup(author_id, thread_id)
            else:
                client.removeUserFromGroup(user.uid, thread_id)
        else:
            message = Message('User not found.')
            client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'perm' or command == 'p':
        if author_id == master_id:
            priority, user = text.split(' ', 1)
            priority = int(priority)
            user = client.matchUser(thread_id, user)
            if not user:
                reply = 'User not found.'
            elif user.uid == master_id:
                reply = 'Cannot modify master priority.'
            elif priority < 0 or priority >= master_priority:
                reply = 'Invalid priority.'
            else:
                priority_set(user.uid, priority)
                reply = user.name + '\'s priority has been set to ' + str(priority)
                reply += ' (' + priority_names[priority] + ').'
        else:
            user = client.fetchUserInfo(author_id)[author_id]
            reply = user.name + '\'s priority has been set to 0'
            reply += ' (' + priority_names[0] + ').'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'quest' or command == 'q':
        if len(text) > 0:
            set_quest_type(client, author, text, thread_id)
        elif author['location'] == 0:
            message = Message('There are no quests to be found here.')
            client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif not check_busy(client, author, thread_id):
            generate_quest(client, author, thread_id)

    elif command == 'random':
        colors = list(ThreadColor)
        group = client.fetchGroupInfo(thread_id)[thread_id]
        color = group.color
        while color == group.color:
            color = random.choice(colors)
        client.changeThreadColor(color, thread_id=thread_id)
        emoji = group.emoji
        while emoji == group.emoji:
            emoji = random_emoji()
        client.changeThreadEmoji(emoji, thread_id=thread_id)

    elif command == 'roll' or command == 'r':
        user = client.fetchUserInfo(author_id)[author_id]
        if len(text) == 0:
            roll = 'a ' + str(random.randint(1, 6))
        elif len(text) > 0 and int(text) > 0:
            roll = str(random.randint(1, int(text)))
            if roll[0] == '8' or (roll[0:2] == '18' and len(roll) % 3 == 2):
                roll = 'an ' + roll
            else:
                roll = 'a ' + roll
        else:
            return
        message = Message(user.name + ' rolls ' + roll + '.')
        client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'scoreboard' or command == 'score':
        group = client.fetchGroupInfo(thread_id)[thread_id].participants
        group = user_get_all_in(list(group))
        users = sorted(group, key=lambda x: calculate_score(x), reverse=True)
        users = [user for user in users if user['_id'] != master_id and user['_id'] != client.uid]
        try:
            page = int(text) - 1
        except:
            page = 0
        if len(users) <= page * 9:
            reply = 'There aren\'t enough users in the chat.'
        else:
            users = users[(page * 9):]
            if len(users) > 9:
                users = users[:9]
            reply = '<<Chat Scoreboard>>'
            for i, user in enumerate(users):
                reply += '\n' + str(page * 9 + i + 1) + '. ' + user['name']
                reply += ' (' + str(calculate_score(user)) + ' points)'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'shop' or command == 's':
        if check_busy(client, author, thread_id):
            return
        elif 'Shop' not in location_features(author['location']):
            message = Message('There is no shop in this location.')
            client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
        elif len(text) == 0:
            generate_shop_info(client, author, thread_id)
        else:
            shop_purchase(client, author, text, thread_id)

    elif command == 'travel' or command == 't':
        if not check_busy(client, author, thread_id):
            if len(text) == 0:
                check_travel(client, author, thread_id)
            else:
                travel_to_location(client, author, text, thread_id)