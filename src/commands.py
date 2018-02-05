from fbchat.models import *
import random
import requests

from emoji import random_emoji
from hearthstone import random_beast
from info import generate_user_info, generate_group_info
from mongo import *
from quest import generate_quest
from util import master_id, priority_names

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
            if not users:
                client.send(Message('Alias not found'), thread_id=author_id)
                return
        else:
            users = alias_get_all()
        reply = []
        for user in users:
            line = '<' + user['name'] + '> (' + user['alias'] + ')\n'
            line += 'Priority: ' + priority_names[user['priority']] + '\n'
            line += 'Gold: ' + str(user['gold'])
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
        elif priority < 0 or priority >= priority_get(master_id):
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
            section += '\n'.join(['"' + i[0] + '": ' + str(i[1]) for i in client.responses])
            reply.append(section)
        reply = '\n\n'.join(reply) if reply else 'No secrets active.'
        client.send(Message(reply), thread_id=author_id)

    elif command == 'wong' or command == 'w':
        text = text.split(' ', 1)
        if len(text) == 2:
            count, text = text
            count = int(count)
            client.responses.append([text, count])
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
                reply = '{} is a cool guy.'.format(user.name)
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
                meessage = Message('User not found.')
                client.send(message, thread_id=thread_id, thread_type=ThreadType.GROUP)
                return
            users = [user.uid]
        else:
            users = client.fetchGroupInfo(thread_id)[thread_id].participants
        reply = []
        for user_id in users:
            user = user_from_id(user_id)
            line = '<' + user['name'] + '>\n'
            line += 'Priority: ' + priority_names[user['priority']] + '\n'
            line += 'Gold: ' + str(user['gold'])
            reply.append(line)
        reply = '\n\n'.join(reply)
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
            elif priority < 0 or priority >= priority_get(master_id):
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
        generate_quest(client, author_id, thread_id)

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

    elif command == 'shop' or command == 's':
        text = text.strip().lower()
        if len(text) == 0:
            reply = ['<<The Wong Shoppe>>']
            reply.append('1. 0100 gold: Charity donation')
            reply.append('2. 1000 gold: Reaction image')
            reply.append('3. 2000 gold: Random hunting pet')
            reply.append('4. 9999 gold: Priority boost')
            reply.append('(Buy things with "!shop <item>")')
            reply = '\n'.join(reply)
        else:
            text = int(text)
            gold = gold_get(author_id)
            if text == 1 and gold >= 100:
                charities = [
                    'Flat Earth Society', 
                    'Westboro Baptist Church', 
                    'Church of Scientology'
                ]
                gold_add(author_id, -100)
                reply = 'The ' + random.choice(charities) + ' thanks you for your donation.'
            elif text == 2 and gold >= 1000:
                gold_add(author_id, -1000)
                image = random.randint(0, client.num_images - 1)
                image_add(author_id, image)
                reply = 'You\'ve received an image! It has been placed in slot '
                reply += str(len(author['images']) + 1) + '.\n'
                reply += '(Use it with "!image <slot>")'
            elif text == 3 and gold >= 2000:
                gold_add(author_id, -2000)
                reply = str(random_beast())
            elif text == 4 and gold >= 9999:
                priority = priority_get(author_id) + 1
                if priority < priority_get(master_id):
                    gold_add(author_id, -9999)
                    priority_set(author_id, priority)
                    name = author['name']
                    reply = name + '\'s rank is now ' + priority_names[priority] + '!'
                else:
                    reply = 'You\'ve already reached the highest rank.'
        client.send(Message(reply), thread_id=thread_id, thread_type=ThreadType.GROUP)