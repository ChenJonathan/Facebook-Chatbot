from fbchat.models import *
from datetime import datetime, timedelta
import math
import random
import requests

from emoji import random_emoji
from hearthstone import random_beast
from info import generate_user_info, generate_group_info
from mongo import *
from quest import generate_quest
from location import check_locations, travel_to_location, explore_location
from util import *

def check_busy(client, user, thread_id):
    if user['_id'] in client.travel_record:
        record = client.travel_record[user['_id']]
        minutes = math.ceil((record[1] - datetime.now()).total_seconds() / 60)
        reply = 'You\'re busy traveling to ' + location_names[record[0]]
        reply += '. (' + str(minutes) + ' minutes remaining).'
    else:
        return False
    client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)
    return True

def run_user_command(client, command, text, author):
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
            line = '<' + user['name'] + '> (' + user['alias'] + ')\n'
            line += 'Priority: ' + priority_names[user['priority']] + '\n'
            line += 'Gold: ' + str(user['gold']) + ' (+' + str(user['gold_rate']) + '/hour)\n'
            line += 'Location: ' + location_names[user['location']]
            if user['_id'] in client.travel_record:
                record = client.travel_record[user['_id']]
                minutes = math.ceil((record[1] - datetime.now()).total_seconds() / 60)
                line += ' -> ' + location_names[record[0]] + '\n'
                line += '(' + str(minutes) + ' minutes remaining)'
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
            section = '< Defines >\n'
            section += '\n'.join(['"' + i + '": ' + j for i, j in client.defines.items()])
            reply.append(section)
        if client.responses:
            section = '< Responses >\n'
            section += '\n'.join(['"' + response + '"' for response in client.responses])
            reply.append(section)
        reply = '\n\n'.join(reply) if reply else 'No secrets active.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'wong' or command == 'w':
        if len(text) > 0:
            client.responses.append(text)
        elif len(text) == 1:
            client.responses.clear()

def run_group_command(client, command, text, author, thread_id):
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
        reply = '<' + user['name'] + '>\n'
        reply += 'Priority: ' + priority_names[user['priority']] + '\n'
        reply += 'Gold: ' + str(user['gold']) + ' (+' + str(user['gold_rate']) + '/hour)\n'
        reply += 'Location: ' + location_names[user['location']]
        if user['_id'] in client.travel_record:
            record = client.travel_record[user['_id']]
            minutes = math.ceil((record[1] - datetime.now()).total_seconds() / 60)
            reply += ' -> ' + location_names[record[0]] + '\n'
            reply += '(' + str(minutes) + ' minutes remaining)'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

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
        if amount < 1:
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

    elif command == 'image' or command == 'i':
        if len(text) > 0:
            slot = int(text)
            images = author['images']
            image = images[slot - 1] if slot > 0 and slot <= len(images) else None
            if image:
                path = './images/' + str(image) + '.jpg'
                client.sendLocalImage(path, thread_id=thread_id, thread_type=ThreadType.GROUP)
        else:
            reply = 'You have ' + str(len(author['images'])) + ' images stored.'
            client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'jail' or command == 'j':
        if author['priority'] >= master_priority - 1:
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
        if author['location'] == 0:
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

    elif command == 'ranking':
        group = client.fetchGroupInfo(thread_id)[thread_id].participants
        group = user_get_all_in(list(group)
        users = sorted(group), key=lambda x: calculate_score(x), reverse=True)
        if len(users) > 9:
            users = users[:9]
        reply = '<<Chat Ranking>>'
        for i, user in enumerate(users):
            reply += '\n' + str(i + 1) + '. ' + user['name']
            reply += ' (' + str(calculate_score(user)) + ' points)'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

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

    elif command == 'shop' or command == 's':
        text = text.strip().lower()
        if len(text) == 0:
            reply = ['<<The Wong Shoppe>>']
            reply.append('1. 0100 gold: Charity donation')
            reply.append('2. 0500 gold: Reaction image')
            reply.append('3. 1000 gold: Random hunting pet')
            reply.append('4. 9999 gold: Priority boost')
            reply.append('(Buy things with "!shop <item>")')
            reply = '\n'.join(reply)
        else:
            text = int(text)
            gold = gold_get(author_id)
            if text == 1:
                if gold >= 100:
                    charities = [
                        'Flat Earth Society', 
                        'Westboro Baptist Church', 
                        'Church of Scientology'
                    ]
                    gold_add(author_id, -100)
                    reply = 'The ' + random.choice(charities) + ' thanks you for your donation.'
                else:
                    reply = 'You can\'t afford that.'
            elif text == 2:
                if gold >= 500:
                    images = author['images']
                    if len(images) == client.num_images:
                        reply = 'You\'ve already bought all the images.'
                    else:
                        gold_add(author_id, -500)
                        image = random.randint(0, client.num_images - 1)
                        while image in images:
                            image = random.randint(0, client.num_images - 1)
                        image_add(author_id, image)
                        reply = 'You\'ve received an image! It has been placed in slot '
                        reply += str(len(author['images']) + 1) + '.\n'
                        reply += '(Use it with "!image <slot>")'
                else:
                    reply = 'You can\'t afford that.'
            elif text == 3:
                if gold >= 1000:
                    beast = random_beast()
                    delta_rate = beast[1] * beast[2]
                    gold_add(author_id, -1000)
                    gold_rate_add(author_id, delta_rate)
                    reply = 'You\'ve bought a ' + str(beast[1]) + '/' + str(beast[2])
                    reply += ' ' + beast[0] + '! It grants you an additional '
                    reply += str(delta_rate) + ' gold per hour.'
                else:
                    reply = 'You can\'t afford that.'
            elif text == 4:
                if gold >= 9999:
                    priority = priority_get(author_id) + 1
                    if priority < master_priority:
                        gold_add(author_id, -9999)
                        priority_set(author_id, priority)
                        name = author['name']
                        reply = name + '\'s rank is now ' + priority_names[priority] + '!'
                    else:
                        reply = 'You\'ve already reached the highest rank.'
                else:
                    reply = 'You can\'t afford that.'
            else:
                return
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)

    elif command == 'travel' or command == 't':
        if not check_busy(client, author, thread_id):
            if len(text) == 0:
                check_locations(client, author, thread_id)
            else:
                travel_to_location(client, author, text, thread_id)